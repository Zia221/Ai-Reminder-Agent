
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./ProgressPage.css";
import { apiRequest } from "../lib/api";

const todayInPakistan = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());

type DailyProgress = {
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

type ProgressHistory = { days: DailyProgress[] };

function displayDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function ProgressPage() {
  const [selectedDay, setSelectedDay] = useState(todayInPakistan);
  const [progress, setProgress] = useState<DailyProgress | null>(null);
  const [history, setHistory] = useState<DailyProgress[]>([]);
  const [goalInput, setGoalInput] = useState("3");
  const [loading, setLoading] = useState(true);
  const [savingGoal, setSavingGoal] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadProgress = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [daily, weekly] = await Promise.all([
        apiRequest<DailyProgress>(
          `/progress/daily?day=${selectedDay}&timezone=Asia%2FKarachi`,
        ),
        apiRequest<ProgressHistory>(
          "/progress/history?days=7&timezone=Asia%2FKarachi",
        ),
      ]);

      setProgress(daily);
      setHistory(weekly.days);
      setGoalInput(String(daily.goal_target));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load progress.");
    } finally {
      setLoading(false);
    }
  }, [selectedDay]);

  useEffect(() => {
    void loadProgress();
  }, [loadProgress]);

  async function saveGoal(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingGoal(true);
    setError("");
    setNotice("");

    try {
      await apiRequest("/progress/goal", {
        method: "PUT",
        body: JSON.stringify({
          goal_date: selectedDay,
          target_tasks: Number(goalInput),
        }),
      });

      setNotice("Daily goal saved!");
      await loadProgress();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the goal.");
    } finally {
      setSavingGoal(false);
    }
  }

  const chartMax = Math.max(
    1,
    ...history.map((item) => item.tasks_completed),
  );

  return (
    <main className="progress-page">
      <header className="progress-header">
        <div>
          <p className="progress-eyebrow">YOUR PRODUCTIVITY</p>
          <h1>Daily Progress</h1>
          <p>Track your tasks, build consistency, and reach your goals.</p>
        </div>
        <Link to="/assistant" className="progress-back-link">
          Back to Assistant
        </Link>
      </header>

      <section className="progress-date-panel">
        <label htmlFor="progress-day">Choose a day</label>
        <input
          id="progress-day"
          type="date"
          value={selectedDay}
          max={todayInPakistan()}
          onChange={(event) => setSelectedDay(event.target.value)}
        />
        <button type="button" onClick={() => setSelectedDay(todayInPakistan())}>
          Today
        </button>
      </section>

      {error && <p className="progress-error" role="alert">{error}</p>}
      {notice && <p className="progress-notice" role="status">{notice}</p>}

      {loading ? (
        <p>Loading your progress...</p>
      ) : progress ? (
        <>
          <section className="progress-stats-grid">
            <article className="progress-stat-card">
              <span>Completed today</span>
              <strong>{progress.tasks_completed}</strong>
            </article>
            <article className="progress-stat-card">
              <span>Tasks due</span>
              <strong>{progress.tasks_due}</strong>
            </article>
            <article className="progress-stat-card">
              <span>Still pending</span>
              <strong>{progress.pending_due}</strong>
            </article>
            <article className="progress-stat-card">
              <span>Overdue</span>
              <strong>{progress.overdue}</strong>
            </article>
          </section>

          <section className="progress-panel">
            <div className="progress-panel-heading">
              <div>
                <h2>Daily completion rate</h2>
                <p>Completed tasks compared with tasks due on this day.</p>
              </div>
              <strong className="progress-percentage">
                {progress.completion_rate}%
              </strong>
            </div>
            <div
              className="progress-track"
              role="progressbar"
              aria-label="Daily completion rate"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progress.completion_rate}
            >
              <div
                className="progress-track-fill"
                style={{
                  width: `${Math.min(100, progress.completion_rate)}%`,
                }}
              />
            </div>
          </section>

          <section className="progress-panel">
            <h2>Daily goal</h2>
            <p>
              {progress.goal_progress} of {progress.goal_target} tasks completed.
            </p>
            <div
              className="progress-track"
              role="progressbar"
              aria-label="Daily goal progress"
              aria-valuemin={0}
              aria-valuemax={progress.goal_target}
              aria-valuenow={Math.min(
                progress.goal_progress,
                progress.goal_target,
              )}
            >
              <div
                className="progress-track-fill"
                style={{
                  width: `${
                    (Math.min(progress.goal_progress, progress.goal_target) /
                      progress.goal_target) *
                    100
                  }%`,
                }}
              />
            </div>

            <p className="progress-goal-status">
              {progress.goal_reached
                ? "Goal reached — great work!"
                : "Keep going. You can reach your goal!"}
            </p>

            <form className="progress-goal-form" onSubmit={saveGoal}>
              <label htmlFor="goal-target">Tasks to complete</label>
              <input
                id="goal-target"
                type="number"
                min="1"
                max="100"
                required
                value={goalInput}
                onChange={(event) => setGoalInput(event.target.value)}
              />
              <button disabled={savingGoal}>
                {savingGoal ? "Saving..." : "Save goal"}
              </button>
            </form>
          </section>

          <section className="progress-panel">
            <h2>Last 7 days</h2>
            <p>Number of tasks completed on each day.</p>

            <div className="progress-chart">
              {history.map((item) => (
                <div className="progress-chart-column" key={item.day}>
                  <span className="progress-chart-value">
                    {item.tasks_completed}
                  </span>
                  <div className="progress-chart-bar-area">
                    <div
                      className="progress-chart-bar"
                      style={{
                        height: `${
                          (item.tasks_completed / chartMax) * 100
                        }%`,
                      }}
                      title={`${item.tasks_completed} tasks completed`}
                    />
                  </div>
                  <span className="progress-chart-label">
                    {displayDate(item.day)}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="progress-panel">
            <h2>Daily history</h2>
            <div className="progress-history-list">
              {[...history].reverse().map((item) => (
                <button
                  className={`progress-history-row ${
                    item.day === selectedDay ? "selected" : ""
                  }`}
                  key={item.day}
                  onClick={() => setSelectedDay(item.day)}
                  type="button"
                >
                  <span>{displayDate(item.day)}</span>
                  <span>{item.tasks_completed} completed</span>
                  <span>{item.completion_rate}% completion</span>
                </button>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}
