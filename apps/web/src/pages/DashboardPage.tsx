import { useEffect, useState } from "react";
import {
  Activity,
  Bell,
  CalendarDays,
  CheckCircle2,
  LayoutDashboard,
  LogOut,
  Menu,
  Sparkles,
  X,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useLocation, useNavigate } from "react-router-dom";
import { apiRequest } from "../lib/api";

const navigation = [
  { label: "Overview", icon: LayoutDashboard, path: "/dashboard" },
  { label: "Reminders", icon: Bell, path: "/reminders" },
  { label: "Daily Progress", icon: Activity, path: "/progress" },
  { label: "Weekly Reports", icon: CalendarDays, path: "/reports" },
  { label: "Project Mentor", icon: Sparkles, path: "/mentor" },
  { label: "Assistant", icon: Sparkles, path: "/assistant" },
  { label: "Smart Planning", icon: CalendarDays, path: "/planning" },
  { label: "Automation", icon: Bell, path: "/automation" },
];

type Reminder = {
  id: number;
  title: string;
  due_at: string | null;
  timezone: string;
  priority: "low" | "medium" | "high" | "urgent";
  status: "pending" | "completed" | "paused" | "cancelled";
  recurrence: "none" | "daily" | "weekly" | "monthly";
};

type Task = {
  id: number;
  title: string;
  due_at: string | null;
  priority: "low" | "medium" | "high" | "urgent";
  status: "pending" | "in_progress" | "completed" | "cancelled";
};

type DailyProgress = {
  tasks_completed: number;
  tasks_due: number;
  goal_target: number;
  goal_progress: number;
  goal_reached: boolean;
};

function todayLabel() {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date());
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [progress, setProgress] = useState<DailyProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadWorkspace() {
      try {
        const [reminderData, taskData, progressData] = await Promise.all([
          apiRequest<Reminder[]>("/reminders"),
          apiRequest<Task[]>("/tasks"),
          apiRequest<DailyProgress>("/progress/daily?timezone=Asia%2FKarachi"),
        ]);

        if (active) {
          setReminders(reminderData);
          setTasks(taskData);
          setProgress(progressData);
          setError("");
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Could not load workspace data.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadWorkspace();
    return () => {
      active = false;
    };
  }, []);

  const displayName = user?.full_name?.trim().split(/\s+/)[0] || "there";
  const initial = displayName.charAt(0).toUpperCase();
  const activePage =
    navigation.find((item) => item.path === location.pathname)?.label || "Overview";
  const activeReminders = reminders.filter((item) => item.status === "pending").length;
  const activeTasks = tasks.filter(
    (item) => item.status === "pending" || item.status === "in_progress",
  );

  function goTo(path: string) {
    setSidebarOpen(false);
    navigate(path);
  }

  return (
    <div className="dashboard-layout">
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <span className="brand-mark">R</span>
          <span>Reminder<span className="brand-light">AI</span></span>
          <button
            className="icon-button sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <X size={19} />
          </button>
        </div>

        <p className="nav-caption">WORKSPACE</p>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navigation.map(({ label, icon: Icon, path }) => (
            <button
              key={path}
              className={`nav-item ${activePage === label ? "nav-active" : ""}`}
              onClick={() => goTo(path)}
            >
              <Icon size={19} />
              <span>{label}</span>
              {label === "Reminders" && <span className="nav-dot" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-user">
            <div className="avatar">{initial}</div>
            <div className="user-details">
              <strong>{user?.full_name || "My Account"}</strong>
              <span>{user?.email}</span>
            </div>
            <button
              className="icon-button"
              aria-label="Log out"
              title="Log out"
              onClick={() => void logout()}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={22} />
          </button>
          <div className="breadcrumb">Workspace <span>/</span> {activePage}</div>
          <div className="topbar-user">
            <div className="avatar avatar-small">{initial}</div>
            <span>{displayName}</span>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">YOUR PERSONAL WORKSPACE</p>
              <h1>Hello, {displayName} <span className="wave">✦</span></h1>
              <p className="muted">A clearer plan. A calmer mind. A better day.</p>
            </div>
            <div className="date-chip">
              <CalendarDays size={17} />
              {todayLabel()}
            </div>
          </section>

          {error && <p className="assistant-alert error" role="alert">{error}</p>}

          <section className="hero-card">
            <div className="hero-copy">
              <span className="hero-badge"><Sparkles size={14} /> YOUR NEXT CHAPTER</span>
              <h2>Your day,<br />organized with AI.</h2>
              <p>
                Manage reminders, track task progress, and use AI tools to organize
                your next productive day.
              </p>
              <button className="button button-light" onClick={() => goTo("/reminders")}>
                Create a reminder <span aria-hidden="true">→</span>
              </button>
            </div>
            <div className="hero-art" aria-hidden="true">
              <div className="art-orbit orbit-one" />
              <div className="art-orbit orbit-two" />
              <div className="art-center"><Sparkles size={38} /></div>
              <div className="art-float float-one"><CheckCircle2 size={21} /></div>
              <div className="art-float float-two"><Activity size={21} /></div>
            </div>
          </section>

          <section className="section-heading">
            <div>
              <h2>Your overview</h2>
              <p className="muted">Live data from your account</p>
            </div>
            <span className="demo-label">Live data</span>
          </section>

          <section className="stats-grid">
            <article className="stat-card">
              <div className="stat-icon icon-purple"><Bell size={20} /></div>
              <p>Active reminders</p>
              <h3>{loading ? "..." : activeReminders}</h3>
              <span className="stat-note">Awaiting completion</span>
            </article>
            <article className="stat-card">
              <div className="stat-icon icon-green"><CheckCircle2 size={20} /></div>
              <p>Tasks completed today</p>
              <h3>{loading ? "..." : progress?.tasks_completed ?? 0}</h3>
              <span className="stat-note">Based on task completion records</span>
            </article>
            <article className="stat-card">
              <div className="stat-icon icon-blue"><Activity size={20} /></div>
              <p>Tasks due today</p>
              <h3>{loading ? "..." : progress?.tasks_due ?? 0}</h3>
              <span className="stat-note">Deadlines scheduled for today</span>
            </article>
            <article className="stat-card">
              <div className="stat-icon icon-orange"><CalendarDays size={20} /></div>
              <p>Daily goal progress</p>
              <h3>{loading ? "..." : `${progress?.goal_progress ?? 0}/${progress?.goal_target ?? 3}`}</h3>
              <span className="stat-note">
                {progress?.goal_reached ? "Goal reached" : "Keep making progress"}
              </span>
            </article>
          </section>

          <section className="bottom-grid">
            <article className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Today's focus</h2>
                  <p className="muted">Your active tasks</p>
                </div>
                <CheckCircle2 size={20} />
              </div>
              {activeTasks.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon"><CalendarDays size={25} /></div>
                  <strong>No active tasks</strong>
                  <p>Create a task or reminder to start planning your day.</p>
                  <button className="button button-light" onClick={() => goTo("/assistant")}>
                    Create a task <span aria-hidden="true">→</span>
                  </button>
                </div>
              ) : (
                <div className="task-list">
                  {activeTasks.slice(0, 5).map((task) => (
                    <article className="task-item" key={task.id}>
                      <div>
                        <h3>{task.title}</h3>
                        <p>
                          {task.priority} · {task.status}
                          {task.due_at ? ` · ${new Date(task.due_at).toLocaleString()}` : ""}
                        </p>
                      </div>
                    </article>
                  ))}
                  <button className="button button-light" onClick={() => goTo("/assistant")}>
                    Manage tasks <span aria-hidden="true">→</span>
                  </button>
                </div>
              )}
            </article>

            <article className="panel mentor-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">AI ASSISTANT</span>
                  <h2>Your productivity partner</h2>
                </div>
                <Sparkles size={22} />
              </div>
              <p className="muted">
                Ask your assistant to propose tasks, get skill-gap insights from
                your mentor, or generate a smart plan for today.
              </p>
              <button className="button button-light" onClick={() => goTo("/assistant")}>
                Open AI assistant <span aria-hidden="true">→</span>
              </button>
            </article>
          </section>

          <footer className="dashboard-footer">
            <span>AI Reminder Agent · Built for meaningful progress</span>
            <span>Local workspace</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
