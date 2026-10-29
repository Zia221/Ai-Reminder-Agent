
import { useState } from "react";
import "./PlanningPage.css";
import { apiRequest as sharedApiRequest } from "../lib/api";

async function apiRequest(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<any> {
  return sharedApiRequest<any>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

function localDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function PlanningPage() {
  const [availableMinutes, setAvailableMinutes] =
    useState(240);

  const [plan, setPlan] = useState<any>(null);
  const [recommendation, setRecommendation] =
    useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generatePlan() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(
        "/planning/generate",
        "POST",
        {
          plan_date: localDateString(),
          available_minutes: availableMinutes,
        }
      );

      setPlan(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadRecommendation() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(
        "/planning/recommendation"
      );

      setRecommendation(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadTodayPlan() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(
        "/planning/today"
      );

      setPlan(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="planning-page">
      <header>
        <h1>Smart Planning</h1>
        <p>
          Plan your day, prioritize tasks, and stay productive.
        </p>
      </header>

      {error && (
        <p className="planning-error">
          {error}
        </p>
      )}

      <section className="planning-card">
        <h2>Generate Your Daily Plan</h2>

        <label>
          Available time (minutes)
        </label>

        <input
          type="number"
          min={30}
          max={960}
          value={availableMinutes}
          onChange={(e) =>
            setAvailableMinutes(
              Number(e.target.value)
            )
          }
        />

        <button
          onClick={generatePlan}
          disabled={loading}
        >
          Generate Plan
        </button>

        <button
          onClick={loadTodayPlan}
          disabled={loading}
        >
          Load Today's Plan
        </button>
      </section>

      <section className="planning-card">
        <h2>Next Task Recommendation</h2>

        <button
          onClick={loadRecommendation}
          disabled={loading}
        >
          Recommend Next Task
        </button>

        {recommendation && (
          <article>
            <h3>{recommendation.title}</h3>
            <p>
              Priority: {recommendation.priority}
            </p>
            <p>{recommendation.reason}</p>
          </article>
        )}
      </section>

      {plan && (
        <section className="planning-card">
          <h2>Daily Plan</h2>

          <p>{plan.summary}</p>

          <p>
            Scheduled tasks: {plan.plan_items.length}
          </p>

          {plan.plan_items.map((item: any) => (
            <article
              key={item.task_id}
              className="plan-item"
            >
              <h3>{item.title}</h3>

              <p>
                {item.start_time} – {item.end_time}
              </p>

              <p>
                Duration: {item.duration_minutes} minutes
              </p>

              <p>
                Priority: {item.priority}
              </p>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
