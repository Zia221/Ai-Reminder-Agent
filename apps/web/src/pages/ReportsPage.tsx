
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./ReportsPage.css";
import { apiRequest } from "../lib/api";

type DailyReportItem = {
  day: string;
  tasks_created: number;
  tasks_completed: number;
  tasks_due: number;
  completed_due: number;
  pending_due: number;
  overdue: number;
  completion_rate: number;
  goal_target: number;
  goal_progress: number;
  goal_reached: boolean;
};

type WeeklyReport = {
  week_start: string;
  week_end: string;
  tasks_created: number;
  tasks_completed: number;
  tasks_due: number;
  completed_due: number;
  pending_due: number;
  overdue: number;
  completion_rate: number;
  goals_reached: number;
  daily_breakdown: DailyReportItem[];
  summary: string;
  summary_is_ai: boolean;
};

async function api<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

function getMonday(date: Date) {
  const monday = new Date(date);
  const day = monday.getDay();
  monday.setDate(monday.getDate() - ((day + 6) % 7));
  monday.setHours(12, 0, 0, 0);
  return monday;
}

function dateString(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function shiftWeek(value: string, amount: number) {
  const date = new Date(`${value}T12:00:00`);
  date.setDate(date.getDate() + amount * 7);
  return dateString(date);
}

function displayDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function ReportsPage() {
  const [weekStart, setWeekStart] = useState(() =>
    dateString(getMonday(new Date())),
  );
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await api<WeeklyReport>(
        `/reports/weekly?week_start=${weekStart}&timezone=Asia%2FKarachi`,
      );
      setReport(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load weekly report.",
      );
    } finally {
      setLoading(false);
    }
  }, [weekStart]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  async function downloadPdf() {
    setDownloading(true);
    setError("");

    try {
      const blob = await apiRequest<Blob>(
        `/reports/weekly/pdf?week_start=${weekStart}&timezone=Asia%2FKarachi`,
      );
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");

      anchor.href = url;
      anchor.download = `weekly-report-${weekStart}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF download failed.");
    } finally {
      setDownloading(false);
    }
  }

  const maxCompleted = Math.max(
    1,
    ...(report?.daily_breakdown.map((item) => item.tasks_completed) ?? []),
  );

  return (
    <main className="reports-page">
      <header className="reports-header">
        <div>
          <p className="reports-eyebrow">PRODUCTIVITY INSIGHTS</p>
          <h1>Weekly Reports</h1>
          <p>Review your progress and see how your week went.</p>
        </div>
        <Link to="/progress" className="reports-link">
          Daily Progress
        </Link>
      </header>

      <section className="reports-controls">
        <button
          type="button"
          onClick={() => setWeekStart((value) => shiftWeek(value, -1))}
        >
          ← Previous week
        </button>

        <div className="reports-week-label">
          {report
            ? `${displayDate(report.week_start)} – ${displayDate(report.week_end)}`
            : weekStart}
        </div>

        <button
          type="button"
          disabled={weekStart >= dateString(getMonday(new Date()))}
          onClick={() => setWeekStart((value) => shiftWeek(value, 1))}
        >
          Next week →
        </button>
      </section>

      {error && <p className="reports-error" role="alert">{error}</p>}

      {loading ? (
        <p>Preparing your weekly report...</p>
      ) : report ? (
        <>
          <section className="reports-stats-grid">
            <article className="reports-stat-card">
              <span>Tasks completed</span>
              <strong>{report.tasks_completed}</strong>
            </article>
            <article className="reports-stat-card">
              <span>Completion rate</span>
              <strong>{report.completion_rate}%</strong>
            </article>
            <article className="reports-stat-card">
              <span>Pending this week</span>
              <strong>{report.pending_due}</strong>
            </article>
            <article className="reports-stat-card">
              <span>Goals reached</span>
              <strong>{report.goals_reached}/7</strong>
            </article>
          </section>

          <section className="reports-panel">
            <div className="reports-panel-heading">
              <div>
                <h2>Weekly task activity</h2>
                <p>Tasks completed each day.</p>
              </div>
              <button
                type="button"
                onClick={downloadPdf}
                disabled={downloading}
              >
                {downloading ? "Preparing PDF..." : "Download PDF"}
              </button>
            </div>

            <div className="reports-chart">
              {report.daily_breakdown.map((item) => (
                <div className="reports-chart-column" key={item.day}>
                  <span className="reports-chart-value">
                    {item.tasks_completed}
                  </span>
                  <div className="reports-chart-area">
                    <div
                      className="reports-chart-bar"
                      style={{
                        height: `${
                          (item.tasks_completed / maxCompleted) * 100
                        }%`,
                      }}
                      title={`${item.tasks_completed} completed`}
                    />
                  </div>
                  <span className="reports-chart-label">
                    {new Date(`${item.day}T12:00:00`).toLocaleDateString(
                      "en-US",
                      { weekday: "short" },
                    )}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="reports-panel">
            <h2>AI weekly summary</h2>
            <p className="reports-summary">{report.summary}</p>
            <p className="reports-summary-source">
              {report.summary_is_ai
                ? "Generated by AI from your weekly statistics."
                : "Statistics-based summary. Configure your AI API key to enable AI-generated insights."}
            </p>
          </section>

          <section className="reports-panel">
            <h2>Daily breakdown</h2>
            <div className="reports-table-wrapper">
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Created</th>
                    <th>Completed</th>
                    <th>Due</th>
                    <th>Pending</th>
                    <th>Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {report.daily_breakdown.map((item) => (
                    <tr key={item.day}>
                      <td>{displayDate(item.day)}</td>
                      <td>{item.tasks_created}</td>
                      <td>{item.tasks_completed}</td>
                      <td>{item.tasks_due}</td>
                      <td>{item.pending_due}</td>
                      <td>{item.completion_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
