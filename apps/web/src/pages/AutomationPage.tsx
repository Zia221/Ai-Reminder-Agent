
import { useEffect, useState } from "react";
import "./AutomationPage.css";
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

type Delivery = {
  id: number;
  task_id: number | null;
  reminder_id: number | null;
  item_title: string | null;
  task_due_at: string | null;
  reminder_due_at: string | null;
  recipient_email: string;
  status: string;
  attempts: number;
  last_error: string | null;
  sent_at: string | null;
  created_at: string;
};

export default function AutomationPage() {
  const [enabled, setEnabled] = useState(true);
  const [emailEnabled, setEmailEnabled] = useState(false);
  const [minutesBefore, setMinutesBefore] = useState(30);

  const [history, setHistory] = useState<Delivery[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadPreferences() {
    try {
      const data = await apiRequest(
        "/reminders/automation/preferences"
      );

      setEnabled(data.enabled);
      setEmailEnabled(data.email_enabled);
      setMinutesBefore(data.minutes_before);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function loadHistory() {
    try {
      const data = await apiRequest(
        "/reminders/automation/history"
      );

      setHistory(data);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function retryDelivery(deliveryId: number) {
    setLoading(true);
    setError("");
    setMessage("");
    try {
      await apiRequest(
        `/reminders/automation/history/${deliveryId}/retry`,
        "POST",
      );
      setMessage("Delivery queued for retry.");
      await loadHistory();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function savePreferences() {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(
        "/reminders/automation/preferences",
        "PUT",
        {
          enabled,
          email_enabled: emailEnabled,
          minutes_before: minutesBefore,
        }
      );

      setMessage("Reminder preferences saved.");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPreferences();
    loadHistory();
  }, []);

  return (
    <main className="automation-page">
      <header>
        <h1>Reminders & Automation</h1>
        <p>
          Configure automatic reminders and review delivery history.
        </p>
      </header>

      {message && (
        <p className="automation-success">{message}</p>
      )}

      {error && (
        <p className="automation-error">{error}</p>
      )}

      <section className="automation-card">
        <h2>Reminder Settings</h2>

        <label className="automation-toggle">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          Enable automatic reminders
        </label>

        <label className="automation-toggle">
          <input
            type="checkbox"
            checked={emailEnabled}
            onChange={(e) => setEmailEnabled(e.target.checked)}
          />
          Send email notifications
        </label>

        <label>
          Remind me before the task is due
        </label>

        <select
          value={minutesBefore}
          onChange={(e) =>
            setMinutesBefore(Number(e.target.value))
          }
        >
          <option value={5}>5 minutes</option>
          <option value={15}>15 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={60}>1 hour</option>
          <option value={120}>2 hours</option>
          <option value={1440}>24 hours</option>
        </select>

        <button
          onClick={savePreferences}
          disabled={loading}
        >
          Save Settings
        </button>
      </section>

      <section className="automation-card">
        <h2>Reminder History</h2>

        <button
          onClick={loadHistory}
          disabled={loading}
        >
          Refresh History
        </button>

        {history.length === 0 && (
          <p>No reminder deliveries yet.</p>
        )}

        {history.map((item) => (
          <article
            className="automation-history-item"
            key={item.id}
          >
            <h3>{item.item_title || (item.reminder_id ? `Reminder #${item.reminder_id}` : `Task #${item.task_id}`)}</h3>

            <p>
              Type: {item.reminder_id ? "Reminder" : "Task"}
            </p>
            <p>
              Due: {new Date(item.reminder_due_at || item.task_due_at || item.created_at).toLocaleString()}
            </p>
            <p>
              Recipient: {item.recipient_email}
            </p>

            <p>
              Status: {item.status}
            </p>

            <p>
              Attempts: {item.attempts}
            </p>

            {item.sent_at && (
              <p>
                Sent: {new Date(item.sent_at).toLocaleString()}
              </p>
            )}

            {item.last_error && (
              <p className="automation-error">
                {item.last_error}
              </p>
            )}
            {item.status === "failed" && (
              <button
                type="button"
                onClick={() => void retryDelivery(item.id)}
                disabled={loading}
              >
                Retry delivery
              </button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
