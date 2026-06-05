// TrainerDashboard.jsx — what a TRAINER sees: their students' overall progress
// and their assignments with submission/review counts. Data comes from
// GET /api/dashboard/trainer.
import { useState, useEffect } from "react";
import DashboardCard from "./DashboardCard.jsx";
import ProgressBar from "./ProgressBar.jsx";
import { getTrainerDashboard } from "../services/api.js";

export default function TrainerDashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getTrainerDashboard().then(setD).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="panel form-error">{error}</div>;
  if (!d) return <div className="panel">Loading dashboard…</div>;

  return (
    <>
      <div className="page-head">
        <h2>Welcome, {d.name}</h2>
        <span className="badge badge-muted">{d.courses.join(", ") || "No courses assigned"}</span>
      </div>

      <section className="card-grid">
        <DashboardCard title="My Students" value={d.totalStudents} />
        <DashboardCard title="Avg Attendance" value={`${d.avgAttendance}%`} />
        <DashboardCard title="Assignments" value={d.assignments.length} />
        <DashboardCard title="Pending Reviews" value={d.pendingReviews} />
      </section>

      <div className="panel" style={{ marginBottom: "1.25rem" }}>
        <h2>Student Progress</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Student</th><th>Course</th><th>Attendance</th><th>Assignments</th><th>Avg Marks</th></tr>
            </thead>
            <tbody>
              {d.students.length === 0 && <tr><td colSpan="5">No students in your courses yet.</td></tr>}
              {d.students.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>{s.course}</td>
                  <td style={{ minWidth: 140 }}><ProgressBar value={s.attendancePct} /></td>
                  <td>{s.submitted}/{s.assignmentsTotal} submitted</td>
                  <td>{s.avgMarks == null ? "—" : s.avgMarks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>My Assignments</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Assignment</th><th>Course</th><th>Due</th><th>Submissions</th><th>To Review</th></tr>
            </thead>
            <tbody>
              {d.assignments.length === 0 && <tr><td colSpan="5">You haven't created any assignments yet.</td></tr>}
              {d.assignments.map((a) => (
                <tr key={a.id}>
                  <td>{a.title}</td>
                  <td>{a.course}</td>
                  <td>{a.due_date || "—"}</td>
                  <td>{a.submissions}</td>
                  <td>
                    {a.pending > 0
                      ? <span className="badge badge-warning">{a.pending} pending</span>
                      : <span className="badge badge-success">all graded</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
