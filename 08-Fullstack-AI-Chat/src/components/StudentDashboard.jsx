// StudentDashboard.jsx — what a STUDENT sees: their own attendance %,
// assignment completion %, average marks, pending work and upcoming classes.
// All numbers come from GET /api/dashboard/student (computed in the database).
import { useState, useEffect } from "react";
import DashboardCard from "./DashboardCard.jsx";
import ProgressBar from "./ProgressBar.jsx";
import { getStudentDashboard } from "../services/api.js";

export default function StudentDashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getStudentDashboard().then(setD).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="panel form-error">{error}</div>;
  if (!d) return <div className="panel">Loading your dashboard…</div>;

  return (
    <>
      <div className="page-head">
        <h2>Welcome, {d.name}</h2>
        <span className="badge badge-muted">{d.course}</span>
      </div>

      <section className="card-grid">
        <DashboardCard title="Attendance" value={`${d.attendancePct}%`} />
        <DashboardCard title="Assignments Done" value={`${d.assignmentPct}%`} />
        <DashboardCard title="Average Marks" value={d.avgMarks == null ? "—" : d.avgMarks} />
        <DashboardCard title="Pending Assignments" value={d.pendingAssignments} />
      </section>

      <section className="panel-grid">
        <div className="panel">
          <h2>My Assignments</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Assignment</th><th>Due</th><th>Status</th><th>Marks</th></tr>
              </thead>
              <tbody>
                {d.assignments.length === 0 && (
                  <tr><td colSpan="4">No assignments yet.</td></tr>
                )}
                {d.assignments.map((a) => (
                  <tr key={a.id}>
                    <td>{a.title}</td>
                    <td>{a.due_date || "—"}</td>
                    <td>
                      <span className={`badge ${a.status === "Graded" ? "badge-success" : a.status === "Submitted" ? "badge-warning" : "badge-muted"}`}>
                        {a.status}
                      </span>
                    </td>
                    <td>{a.marks == null ? "—" : `${a.marks}/${a.max_marks}`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <h2>Attendance</h2>
          <ProgressBar value={d.attendancePct} />
          <p className="muted-line">{d.present} of {d.totalClasses} classes attended</p>

          <h2 style={{ marginTop: "1.25rem" }}>Upcoming Classes</h2>
          {d.upcomingClasses.length === 0 && <p className="muted-line">None scheduled.</p>}
          <ul className="activity-list">
            {d.upcomingClasses.map((c, i) => (
              <li key={i}>
                <strong>{c.title}</strong><br />
                <span className="muted-line">{c.scheduled_at}</span>{" "}
                <a className="btn btn-sm" href={c.meet_link} target="_blank" rel="noreferrer">Join</a>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
