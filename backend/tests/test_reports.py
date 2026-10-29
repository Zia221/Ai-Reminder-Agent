
from datetime import datetime
from zoneinfo import ZoneInfo


def test_weekly_report_requires_auth(client):
    response = client.get("/api/v1/reports/weekly")
    assert response.status_code == 401


def test_weekly_report_returns_seven_daily_items(client, auth_headers):
    response = client.get(
        "/api/v1/reports/weekly?timezone=Asia%2FKarachi",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["daily_breakdown"]) == 7
    assert data["week_start"]
    assert data["week_end"]
    assert data["completion_rate"] >= 0
    assert isinstance(data["summary"], str)


def test_weekly_report_pdf_returns_pdf(client, auth_headers):
    response = client.get(
        "/api/v1/reports/weekly/pdf?timezone=Asia%2FKarachi",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_weekly_report_rejects_invalid_timezone(client, auth_headers):
    response = client.get(
        "/api/v1/reports/weekly?timezone=NotARealTimezone",
        headers=auth_headers,
    )

    assert response.status_code == 422
