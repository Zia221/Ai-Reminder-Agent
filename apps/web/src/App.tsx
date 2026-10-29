
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";

import ProtectedRoute from "./components/ProtectedRoute";
import WorkspaceLayout from "./components/WorkspaceLayout";
import PlanningPage from "./pages/PlanningPage";
import AssistantPage from "./pages/AssistantPage";
import AutomationPage from "./pages/AutomationPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import MentorPage from "./pages/MentorPage";
import ProgressPage from "./pages/ProgressPage";
import RegisterPage from "./pages/RegisterPage";
import RemindersPage from "./pages/RemindersPage";
import ReportsPage from "./pages/ReportsPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Default route */}
          <Route
            path="/"
            element={<Navigate to="/dashboard" replace />}
          />

          {/* Public routes */}
          <Route
            path="/login"
            element={<LoginPage />}
          />

          <Route
            path="/register"
            element={<RegisterPage />}
          />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route
              path="/dashboard"
              element={<DashboardPage />}
            />
            
<Route
  path="/planning"
  element={
  <WorkspaceLayout>
  <PlanningPage />
  </WorkspaceLayout>
  }

            />
            {/* AI Project Mentor */}
            <Route
              path="/mentor"
              element={
                <WorkspaceLayout>
                  <MentorPage />
                </WorkspaceLayout>
              }
            />
            <Route
  path="/automation"
  element={
    <WorkspaceLayout>
      <AutomationPage />
    </WorkspaceLayout>
  }
/>

            <Route
              path="/progress"
              element={
                <WorkspaceLayout>
                  <ProgressPage />
                </WorkspaceLayout>
              }
            />

            <Route
              path="/reminders"
              element={
                <WorkspaceLayout>
                  <RemindersPage />
                </WorkspaceLayout>
              }
            />

            <Route
              path="/assistant"
              element={
                <WorkspaceLayout>
                  <AssistantPage />
                </WorkspaceLayout>
              }
            />

            {/* Weekly Reports */}
            <Route
              path="/reports"
              element={
                <WorkspaceLayout>
                  <ReportsPage />
                </WorkspaceLayout>
              }
            />
          </Route>

          {/* Unknown routes */}
          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
