
import { useState,useEffect } from "react";
import "./MentorPage.css";
import ReactMarkdown from "react-markdown";
import { apiRequest as sharedApiRequest } from "../lib/api";
async function apiRequest(path: string, method = "GET", body?: unknown): Promise<any> {
  return sharedApiRequest<any>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export default function MentorPage() {

  const [targetRole, setTargetRole] = useState("Agentic AI Engineer");
  const [experience, setExperience] = useState("beginner");
  const [skills, setSkills] = useState("Python, FastAPI, SQL, Git");
  const [goals, setGoals] = useState(
    "Learn AI agents, RAG, MCP, and LangGraph"
  );

  const [profile, setProfile] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [roadmap, setRoadmap] = useState<any>(null);
  useEffect(() => {
  async function loadRoadmap() {
    try {
      const data = await apiRequest("/mentor/roadmap");
      setRoadmap(data);
    } catch (err) {
      // No saved roadmap yet, so nothing to load.
    }
  }

  loadRoadmap();
}, []);

  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function saveProfile() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/mentor/profile", "POST", {
        target_role: targetRole,
        experience_level: experience,
        current_skills: skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
        learning_goals: goals,
      });

      setProfile(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function analyzeSkills() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/mentor/analyze", "POST");
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function generateRoadmap() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/mentor/roadmap", "POST");
      setRoadmap(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function updateMilestone(id: string, status: string) {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(
        `/mentor/milestones/${id}`,
        "PATCH",
        { status }
      );

      setRoadmap(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function askMentor() {
    if (!question.trim()) return;

    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/mentor/chat", "POST", {
        message: question,
      });

      setReply(data.reply);
      setQuestion("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const milestones = roadmap?.milestones || [];
  const completed = milestones.filter(
    (item: any) => item.status === "completed"
  ).length;

  const progress = milestones.length
    ? Math.round((completed / milestones.length) * 100)
    : 0;

  return (
    <main className="mentor-page">
      <header>
        <h1>AI Project Mentor</h1>
        <p>
          Analyze your skills, discover skill gaps, and generate
          your personalized learning roadmap.
        </p>
      </header>

      {error && <p className="error-message">{error}</p>}

      <section className="mentor-card">
        <h2>Your Skill Profile</h2>

        <label>Target role</label>
        <input
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
        />

        <label>Experience level</label>
        <select
          value={experience}
          onChange={(e) => setExperience(e.target.value)}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        <label>Current skills (comma-separated)</label>
        <input
          value={skills}
          onChange={(e) => setSkills(e.target.value)}
        />

        <label>Learning goals</label>
        <textarea
          value={goals}
          onChange={(e) => setGoals(e.target.value)}
        />

        <button onClick={saveProfile} disabled={loading}>
          Save Profile
        </button>

        <button onClick={analyzeSkills} disabled={loading}>
          Analyze Skill Gaps
        </button>

        <button onClick={generateRoadmap} disabled={loading}>
          Generate Roadmap
        </button>

        {profile && <p>Skill profile saved successfully.</p>}
      </section>

      {analysis && (
        <section className="mentor-card">
          <h2>Skill Gap Analysis</h2>
          <p>{analysis.summary}</p>

          {analysis.skill_gaps.map((gap: any, index: number) => (
            <article key={index}>
              <h3>{gap.skill}</h3>
              <p>
                Current: {gap.current_level} | Target: {gap.target_level}
              </p>
              <p>Importance: {gap.importance}</p>
              <p>{gap.reason}</p>
            </article>
          ))}
        </section>
      )}

      {roadmap && (
        <section className="mentor-card">
          <h2>{roadmap.title}</h2>
          <p>{roadmap.description}</p>

          <h3>Roadmap Progress: {progress}%</h3>

          <progress value={progress} max="100" />

          {milestones.map((milestone: any) => (
            <article key={milestone.id}>
              <h3>{milestone.title}</h3>
              <p>{milestone.description}</p>
              <p>
                Estimated duration: {milestone.estimated_days} days
              </p>

              <select
                value={milestone.status}
                onChange={(e) =>
                  updateMilestone(milestone.id, e.target.value)
                }
              >
                <option value="not_started">Not Started</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </article>
          ))}
        </section>
      )}

      <section className="mentor-card">
        <h2>Ask Your AI Mentor</h2>

        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What should I learn next?"
        />

        <button onClick={askMentor} disabled={loading}>
          Ask Mentor
        </button>

{reply && (
  <div className="mentor-reply">
    <ReactMarkdown>{reply}</ReactMarkdown>
  </div>
)}      </section>
    </main>
  );
}
