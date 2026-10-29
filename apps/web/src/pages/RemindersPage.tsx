
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./RemindersPage.css";
import { apiRequest as sharedApiRequest } from "../lib/api";
import type { FormEvent } from "react";
type Priority = "low" | "medium" | "high" | "urgent";
type ReminderStatus = "pending" | "completed" | "paused" | "cancelled";
type Recurrence = "none" | "daily" | "weekly" | "monthly";

interface Reminder {
  id: number;
  title: string;
  description: string | null;
  due_at: string | null;
  timezone: string;
  priority: Priority;
  status: ReminderStatus;
  recurrence: Recurrence;
  natural_language_input: string | null;
  completed_at: string | null;
  created_at: string;
}

interface Draft {
  title: string;
  description: string;
  due_at: string;
  timezone: string;
  priority: Priority;
  recurrence: Recurrence;
  natural_language_input: string;
}

const EMPTY_DRAFT: Draft = {
  title: "",
  description: "",
  due_at: "",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  priority: "medium",
  recurrence: "none",
  natural_language_input: "",
};

async function reminderRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return sharedApiRequest<T>(path, options);
}
function timezoneParts(value: Date, timezone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(value);
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

function toLocalInput(value: string | null, timezone: string): string {
  if (!value) return "";
  const parts = timezoneParts(new Date(value), timezone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** Convert a datetime-local value in the selected IANA timezone to UTC ISO. */
function localDateTimeToISO(value: string, timezone: string): string {
  const [datePart, timePart] = value.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  const target = Date.UTC(year, month - 1, day, hour, minute);
  let guess = target;

  for (let attempt = 0; attempt < 4; attempt += 1) {
    const parts = timezoneParts(new Date(guess), timezone);
    const represented = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
    );
    const offset = represented - guess;
    if (offset === 0) break;
    guess = target - offset;
  }

  return new Date(guess).toISOString();
}

function formatDueDate(value: string | null, timezone: string): string {
  if (!value) return "No due date";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: timezone,
  }).format(new Date(value));
}

export default function RemindersPage() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [naturalText, setNaturalText] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadReminders = useCallback(async () => {
    setLoading(true);
    try {
      const result = await reminderRequest<Reminder[]>("/reminders");
      setReminders(result);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load reminders.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReminders();
  }, [loadReminders]);

  function changeDraft<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function interpretWithAI(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setWorking(true);

    try {
      const result = await reminderRequest<{
        title: string;
        description: string | null;
        due_at: string | null;
        timezone: string;
        priority: Priority;
        recurrence: Recurrence;
        natural_language_input: string;
      }>("/reminders/parse", {
        method: "POST",
        body: JSON.stringify({
          text: naturalText,
          timezone: draft.timezone,
        }),
      });

      setDraft({
        title: result.title,
        description: result.description ?? "",
        due_at: toLocalInput(result.due_at, result.timezone),
        timezone: result.timezone,
        priority: result.priority,
        recurrence: result.recurrence,
        natural_language_input: result.natural_language_input,
      });
      setNotice("AI interpreted your request. Review the details before saving.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "AI parsing failed.");
    } finally {
      setWorking(false);
    }
  }

  async function createReminder(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setWorking(true);

    try {
      const dueAt = draft.due_at
        ? localDateTimeToISO(draft.due_at, draft.timezone)
        : null;

      await reminderRequest<Reminder>("/reminders", {
        method: "POST",
        body: JSON.stringify({
          title: draft.title,
          description: draft.description.trim() || null,
          due_at: dueAt,
          timezone: draft.timezone,
          priority: draft.priority,
          recurrence: draft.recurrence,
          natural_language_input: draft.natural_language_input || null,
        }),
      });

      setDraft({ ...EMPTY_DRAFT, timezone: draft.timezone });
      setNaturalText("");
      setNotice("Reminder saved successfully.");
      await loadReminders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save reminder.");
    } finally {
      setWorking(false);
    }
  }

  async function runAction(
    id: number,
    action: "pause" | "resume" | "complete" | "delete",
  ) {
    if (
      action === "delete" &&
      !window.confirm("Delete this reminder permanently?")
    ) {
      return;
    }

    setError("");
    setNotice("");

    try {
      await reminderRequest<void>(
        `/reminders/${id}${action === "delete" ? "" : `/${action}`}`,
        { method: action === "delete" ? "DELETE" : "POST" },
      );
      setNotice(
        action === "delete"
          ? "Reminder deleted."
          : `Reminder ${action === "complete" ? "completed" : `${action}d`}.`,
      );
      await loadReminders();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    }
  }

  return (
    <main className="reminders-page">
      <header className="reminders-header">
        <div>
          <p className="reminders-eyebrow">YOUR PRODUCTIVITY WORKSPACE</p>
          <h1>My reminders</h1>
          <p>Create reminders manually or describe what you need in plain English.</p>
        </div>
        <div className="reminders-header-actions">
          <Link to="/automation" className="reminders-back">Automation settings</Link>
          <Link to="/dashboard" className="reminders-back">Back to dashboard</Link>
        </div>
      </header>

      {error && <div className="reminder-alert error" role="alert">{error}</div>}
      {notice && <div className="reminder-alert success" role="status">{notice}</div>}

      <section className="reminder-panel">
        <h2>Ask AI to understand your reminder</h2>
        <p>
          Example: “Remind me tomorrow at 9 AM to study Python, high priority.”
        </p>
        <form onSubmit={interpretWithAI}>
          <label htmlFor="natural-text">Describe your reminder</label>
          <textarea
            id="natural-text"
            value={naturalText}
            onChange={(event) => setNaturalText(event.target.value)}
            minLength={3}
            maxLength={1000}
            required
            placeholder="Remind me every Monday at 9 AM to practice FastAPI..."
          />
          <button disabled={working} type="submit">
            {working ? "Thinking..." : "Interpret with AI"}
          </button>
        </form>
      </section>

      <section className="reminder-panel">
        <h2>Review and save</h2>
        <form className="reminder-form" onSubmit={createReminder}>
          <label>
            Title
            <input
              value={draft.title}
              onChange={(event) => changeDraft("title", event.target.value)}
              maxLength={200}
              required
            />
          </label>

          <label>
            Description
            <textarea
              value={draft.description}
              onChange={(event) => changeDraft("description", event.target.value)}
            />
          </label>

          <label>
            Due date and time
            <input
              type="datetime-local"
              value={draft.due_at}
              onChange={(event) => changeDraft("due_at", event.target.value)}
            />
          </label>

          <label>
            Timezone
            <input
              value={draft.timezone}
              onChange={(event) => changeDraft("timezone", event.target.value)}
              required
            />
          </label>

          <label>
            Priority
            <select
              value={draft.priority}
              onChange={(event) =>
                changeDraft("priority", event.target.value as Priority)
              }
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>

          <label>
            Recurrence
            <select
              value={draft.recurrence}
              onChange={(event) =>
                changeDraft("recurrence", event.target.value as Recurrence)
              }
            >
              <option value="none">Does not repeat</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </label>

          <button disabled={working} type="submit">
            {working ? "Saving..." : "Save reminder"}
          </button>
        </form>
      </section>

      <section className="reminder-panel">
        <div className="reminders-list-header">
          <h2>Your reminders</h2>
          <button type="button" onClick={() => void loadReminders()}>
            Refresh
          </button>
        </div>

        {loading ? (
          <p>Loading reminders...</p>
        ) : reminders.length === 0 ? (
          <p>You don't have any reminders yet. Create your first one above.</p>
        ) : (
          <div className="reminder-list">
            {reminders.map((reminder) => (
              <article className="reminder-card" key={reminder.id}>
                <div className="reminder-card-top">
                  <div>
                    <h3>{reminder.title}</h3>
                    {reminder.description && <p>{reminder.description}</p>}
                  </div>
                  <span className={`reminder-status ${reminder.status}`}>
                    {reminder.status}
                  </span>
                </div>

                <p className="reminder-meta">
                  Due: {formatDueDate(reminder.due_at, reminder.timezone)}
                  {" · "}Priority: {reminder.priority}
                  {" · "}Repeats: {reminder.recurrence}
                </p>

                <div className="reminder-actions">
                  {reminder.status === "pending" && (
                    <>
                      <button onClick={() => void runAction(reminder.id, "pause")}>
                        Pause
                      </button>
                      <button onClick={() => void runAction(reminder.id, "complete")}>
                        Complete
                      </button>
                    </>
                  )}
                  {reminder.status === "paused" && (
                    <button onClick={() => void runAction(reminder.id, "resume")}>
                      Resume
                    </button>
                  )}
                  <button
                    className="danger"
                    onClick={() => void runAction(reminder.id, "delete")}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
