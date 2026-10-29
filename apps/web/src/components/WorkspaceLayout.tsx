import { useState, type ReactNode } from "react";
import {
  Activity,
  Bell,
  CalendarDays,
  LayoutDashboard,
  LogOut,
  Menu,
  Sparkles,
  X,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const navigation = [
  { label: "Overview", icon: LayoutDashboard, path: "/dashboard" },
  { label: "Smart Planning", icon: CalendarDays, path: "/planning" },
  { label: "Reminders & Automation", icon: Bell, path: "/automation" },
  { label: "Reminders", icon: Bell, path: "/reminders" },
  { label: "Daily Progress", icon: Activity, path: "/progress" },
  { label: "Weekly Reports", icon: CalendarDays, path: "/reports" },
  { label: "AI Project Mentor", icon: Sparkles, path: "/mentor" },
  { label: "Assistant", icon: Sparkles, path: "/assistant" },
];

export default function WorkspaceLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const displayName = user?.full_name?.trim().split(/\s+/)[0] || "there";
  const initial = displayName.charAt(0).toUpperCase();

  const currentPage =
    navigation.find((item) => item.path === location.pathname)?.label ||
    "Workspace";

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
          <span>
            Reminder<span className="brand-light">AI</span>
          </span>
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
            <NavLink
              key={path}
              to={path}
              end
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-active" : ""}`
              }
              onClick={() => setSidebarOpen(false)}
            >
              <Icon size={19} />
              <span>{label}</span>
              {label === "Reminders" && <span className="nav-dot" />}
            </NavLink>
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

          <div className="breadcrumb">
            Workspace <span>/</span> {currentPage}
          </div>

          <div className="topbar-user">
            <div className="avatar avatar-small">{initial}</div>
            <span>{displayName}</span>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}
