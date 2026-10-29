
from datetime import date, datetime
from io import BytesIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import WeeklyReportRead
from app.services.report_service import (
    build_weekly_report,
    get_week_dates,
)
from sqlalchemy.orm import Session


router = APIRouter(prefix="/reports", tags=["reports"])


def validate_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Invalid timezone. Use an IANA timezone such as Asia/Karachi.",
        )


def get_selected_week(
    week_start: date | None,
    timezone_name: str,
) -> date:
    zone = validate_timezone(timezone_name)
    selected = week_start or datetime.now(zone).date()
    monday, _ = get_week_dates(selected)
    return monday


@router.get("/weekly", response_model=WeeklyReportRead)
def weekly_report(
    week_start: date | None = None,
    timezone_name: str = Query(
        default="Asia/Karachi",
        alias="timezone",
        max_length=64,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_week = get_selected_week(week_start, timezone_name)

    return build_weekly_report(
        db=db,
        user_id=current_user.id,
        week_start=selected_week,
        timezone_name=timezone_name,
    )


def create_weekly_pdf(report: WeeklyReportRead) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="AI Reminder Agent - Weekly Productivity Report",
        author="AI Reminder Agent",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4338CA"),
        fontSize=20,
        leading=25,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
        fontSize=10,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#312E81"),
        fontSize=13,
        leading=17,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        alignment=TA_LEFT,
    )

    story = [
        Paragraph("Weekly Productivity Report", title_style),
        Paragraph(
            f"{report.week_start.isoformat()} to "
            f"{report.week_end.isoformat()}",
            subtitle_style,
        ),
    ]

    summary_data = [
        ["Tasks created", "Tasks completed", "Completion rate"],
        [
            str(report.tasks_created),
            str(report.tasks_completed),
            f"{report.completion_rate}%",
        ],
        ["Tasks due", "Pending tasks", "Overdue"],
        [
            str(report.tasks_due),
            str(report.pending_due),
            str(report.overdue),
        ],
        ["Daily goals reached", "", ""],
        [str(report.goals_reached), "", ""],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[2.2 * inch, 2.2 * inch, 2.2 * inch],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.extend(
        [
            summary_table,
            Spacer(1, 16),
            Paragraph("Daily Breakdown", section_style),
        ]
    )

    daily_data = [
        [
            "Day",
            "Created",
            "Completed",
            "Due",
            "Pending",
            "Rate",
        ]
    ]

    for item in report.daily_breakdown:
        daily_data.append(
            [
                item.day.strftime("%a, %b %d"),
                str(item.tasks_created),
                str(item.tasks_completed),
                str(item.tasks_due),
                str(item.pending_due),
                f"{item.completion_rate}%",
            ]
        )

    daily_table = Table(
        daily_data,
        repeatRows=1,
        colWidths=[
            1.35 * inch,
            0.75 * inch,
            0.85 * inch,
            0.65 * inch,
            0.85 * inch,
            0.65 * inch,
        ],
    )

    daily_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F8FAFC"),
                ]),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.extend(
        [
            daily_table,
            Spacer(1, 14),
            Paragraph("Weekly Summary", section_style),
            Paragraph(escape(report.summary), body_style),
            Spacer(1, 12),
            Paragraph(
                "Generated by AI Reminder Agent",
                ParagraphStyle(
                    "ReportFooter",
                    parent=styles["Normal"],
                    alignment=TA_CENTER,
                    fontSize=8,
                    textColor=colors.HexColor("#64748B"),
                ),
            ),
        ]
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@router.get("/weekly/pdf")
def weekly_report_pdf(
    week_start: date | None = None,
    timezone_name: str = Query(
        default="Asia/Karachi",
        alias="timezone",
        max_length=64,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_week = get_selected_week(week_start, timezone_name)

    report = build_weekly_report(
        db=db,
        user_id=current_user.id,
        week_start=selected_week,
        timezone_name=timezone_name,
    )

    pdf_bytes = create_weekly_pdf(report)

    filename = f"weekly-report-{report.week_start.isoformat()}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
