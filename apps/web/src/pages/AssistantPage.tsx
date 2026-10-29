
import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import "./AssistantPage.css";
import { apiRequest } from "../lib/api";

type Priority = "low" | "medium" | "high" | "urgent";
type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";

interface Task {
  id: number;
  title: string;
  description: string | null;
  due_at: string | null;
  priority: Priority;
  status: TaskStatus;
}

interface SuggestedTask {
  title: string;
  description: string | null;
  due_at: string | null;
  priority: Priority;
}

interface ChatResponse {
  reply: string;
  action: "none" | "create_task";
  suggested_task: SuggestedTask | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  proposal?: SuggestedTask;
}

export default function AssistantPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [dueAt, setDueAt] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadTasks = useCallback(async () => {
    const result = await apiRequest<Task[]>("/tasks");
    setTasks(result);
  }, []);

  const loadHistory = useCallback(async () => {
    const result = await apiRequest<
      { role: "user" | "assistant"; content: string }[]
    >("/assistant/history");

    setMessages(
      result.map((item) => {
        if (item.role === "assistant") {
          try {
            const parsed = JSON.parse(item.content) as ChatResponse;
            return {
              role: "assistant" as const,
              content: parsed.reply,
              proposal:
                parsed.action === "create_task"
                  ? parsed.suggested_task ?? undefined
                  : undefined,
            };
          } catch {
            return { role: "assistant" as const, content: item.content };
          }
        }
        return { role: "user" as const, content: item.content };
      }),
    );
  }, []);

  useEffect(() => {
    async function loadPage() {
      try {
        await Promise.all([loadTasks(), loadHistory()]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load the page.");
      } finally {
        setLoading(false);
      }
    }
    void loadPage();
  }, [loadHistory, loadTasks]);

  async function createTask(
    task: SuggestedTask | {
      title: string;
      description: string | null;
      due_at: string | null;
      priority: Priority;
    },
  ) {
    await apiRequest<Task>("/tasks", {
      method: "POST",
      body: JSON.stringify(task),
    });
    await loadTasks();
    setNotice(`Task "${task.title}" created.`);
  }

  async function submitManualTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");

    try {
      const dueAtISO = dueAt ? new Date(dueAt).toISOString() : null;
      await createTask({
        title: taskTitle,
        description: taskDescription.trim() || null,
        due_at: dueAtISO,
        priority,
      });
      setTaskTitle("");
      setTaskDescription("");
      setDueAt("");
      setPriority("medium");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create task.");
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = message.trim();
    if (!text || sending) return;

    setError("");
    setNotice("");
    setSending(true);
    setMessages((current) => [...current, { role: "user", content: text }]);
    setMessage("");

    try {
      const result = await apiRequest<ChatResponse>("/assistant/chat", {
        method: "POST",
        body: JSON.stringify({ message: text }),
      });

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: result.reply,
          proposal:
            result.action === "create_task"
              ? result.suggested_task ?? undefined
              : undefined,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assistant request failed.");
    } finally {
      setSending(false);
    }
  }

  async function completeTask(taskId: number) {
    setError("");
    try {
      await apiRequest<Task>(`/tasks/${taskId}/complete`, {
        method: "POST",
      });
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not complete task.");
    }
  }

  async function deleteTask(taskId: number) {
    if (!window.confirm("Delete this task permanently?")) return;

    setError("");
    try {
      await apiRequest<void>(`/tasks/${taskId}`, { method: "DELETE" });
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete task.");
    }
  }

  async function clearHistory() {
    if (!window.confirm("Delete your saved assistant conversation history?")) {
      return;
    }
    try {
      await apiRequest<void>("/assistant/history", { method: "DELETE" });
      setMessages([]);
      setNotice("Conversation history cleared.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear history.");
    }
  }

  return (
    <main className="assistant-page">
      <header className="assistant-header">
        <div>
          <p className="assistant-eyebrow">AI REMINDER AGENT</p>
          <h1>Personal Assistant</h1>
          <p>Organize tasks, choose priorities, and plan your next step.</p>
        </div>
        <Link to="/dashboard">Back to dashboard</Link>
      </header>

      {error && <div className="assistant-alert error" role="alert">{error}</div>}
      {notice && <div className="assistant-alert success" role="status">{notice}</div>}

      {loading ? (
        <p>Loading your workspace...</p>
      ) : (
        <div className="assistant-layout">
          <section className="assistant-panel chat-panel">
            <div className="assistant-panel-heading">
              <div>
                <h2>Chat with your assistant</h2>
                <p>The assistant proposes actions; you approve them.</p>
              </div>
              <button className="secondary-button" onClick={() => void clearHistory()}>
                Clear history
              </button>
            </div>

            <div className="chat-messages" aria-live="polite">
              {messages.length === 0 && (
                <div className="chat-empty">
                  <h3>What would you like to work on?</h3>
                  <p>Try: “Help me plan my day” or “Create a task to study Python.”</p>
                </div>
              )}

              {messages.map((item, index) => (
                <article className={`chat-bubble ${item.role}`} key={`${index}-${item.role}`}>
                  <strong>{item.role === "user" ? "You" : "Assistant"}</strong>
                  <p>{item.content}</p>

                  {item.proposal && (
                    <div className="task-proposal">
                      <h3>Proposed task</h3>
                      <p><strong>{item.proposal.title}</strong></p>
                      {item.proposal.description && <p>{item.proposal.description}</p>}
                      <p>Priority: {item.proposal.priority}</p>
                      <p>
                        Due: {item.proposal.due_at
                          ? new Date(item.proposal.due_at).toLocaleString()
                          : "Not specified"}
                      </p>
                      <button
                        onClick={async () => {
                          try {
                            await createTask(item.proposal!);
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Could not create task.");
                          }
                        }}
                      >
                        Confirm and create task
                      </button>
                    </div>
                  )}
                </article>
              ))}

              {sending && <p className="assistant-thinking">Thinking...</p>}
            </div>

            <form className="chat-input-row" onSubmit={sendMessage}>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Ask your assistant..."
                rows={2}
                maxLength={4000}
                required
              />
              <button disabled={sending || !message.trim()}>
                {sending ? "Sending..." : "Send"}
              </button>
            </form>
          </section>

          <aside className="assistant-side">
            <section className="assistant-panel">
              <h2>Create a task</h2>
              <form className="manual-task-form" onSubmit={submitManualTask}>
                <label>
                  Task title
                  <input
                    value={taskTitle}
                    onChange={(event) => setTaskTitle(event.target.value)}
                    maxLength={200}
                    required
                  />
                </label>
                <label>
                  Description
                  <textarea
                    value={taskDescription}
                    onChange={(event) => setTaskDescription(event.target.value)}
                  />
                </label>
                <label>
                  Deadline
                  <input
                    type="datetime-local"
                    value={dueAt}
                    onChange={(event) => setDueAt(event.target.value)}
                  />
                </label>
                <label>
                  Priority
                  <select
                    value={priority}
                    onChange={(event) => setPriority(event.target.value as Priority)}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </label>
                <button>Create task</button>
              </form>
            </section>

            <section className="assistant-panel">
              <div className="assistant-panel-heading">
                <h2>Your tasks ({tasks.length})</h2>
                <button className="secondary-button" onClick={() => void loadTasks()}>
                  Refresh
                </button>
              </div>

              {tasks.length === 0 ? (
                <p>No tasks yet. Create your first task above.</p>
              ) : (
                <div className="task-list">
                  {tasks.map((task) => (
                    <article className="task-item" key={task.id}>
                      <div>
                        <h3>{task.title}</h3>
                        <p>
                          {task.priority} · {task.status}
                          {task.due_at
                            ? ` · ${new Date(task.due_at).toLocaleString()}`
                            : ""}
                        </p>
                      </div>
                      <div className="task-item-actions">
                        {task.status !== "completed" && task.status !== "cancelled" && (
                          <button onClick={() => void completeTask(task.id)}>
                            Complete
                          </button>
                        )}
                        <button
                          className="danger-button"
                          onClick={() => void deleteTask(task.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </aside>
        </div>
      )}
    </main>
  );
}
