// MyProgress.jsx — a student's own detail page: every attendance record and
// every graded submission. Reads GET /api/attendance/me and /api/submissions/me.
import { useState, useEffect } from "react";
import ProgressBar from "../components/ProgressBar.jsx";
import { getMyAttendance, getMySubmissions } from "../services/api.js";

export default function MyProgress() {
  const [attendance, setAttendance] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getMyAttendance(), getMySubmissions()])
      .then(([att, subs]) => { setAttendance(att); setSubmissions(subs); })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="panel form-error">{error}</div>;

  const present = attendance.filter((a) => a.status === "Present").length;
  const attPct = attendance.length ? Math.round((present / attendance.length) * 100) : 0;
  const graded = submissions.filter((s) => s.status === "Graded" && s.marks != null);
  const avg = graded.length ? Math.round(graded.reduce((t, s) => t + s.marks, 0) / graded.length) : null;

  return (
    <>
      <div className="page-head"><h2>My Progress</h2></div>

      <div className="panel" style={{ marginBottom: "1.25rem" }}>
        <h2>Attendance — {present}/{attendance.length} classes ({attPct}%)</h2>
        <ProgressBar value={attPct} />
        <div className="table-wrap" style={{ marginTop: ".75rem" }}>
          <table>
            <thead><tr><th>Date</th><th>Course</th><th>Status</th><th>Marked By</th></tr></thead>
            <tbody>
              {attendance.length === 0 && <tr><td colSpan="4">No attendance recorded yet.</td></tr>}
              {attendance.map((a) => (
                <tr key={a.id}>
                  <td>{a.date}</td>
                  <td>{a.course}</td>
                  <td><span className={`badge ${a.status === "Present" ? "badge-success" : "badge-muted"}`}>{a.status}</span></td>
                  <td>{a.marked_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Marks {avg != null && <span className="muted-line">· average {avg}</span>}</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Assignment</th><th>Status</th><th>Marks</th><th>Feedback</th></tr></thead>
            <tbody>
              {submissions.length === 0 && <tr><td colSpan="4">No submissions yet.</td></tr>}
              {submissions.map((s) => (
                <tr key={s.id}>
                  <td>{s.assignment_title}</td>
                  <td><span className={`badge ${s.status === "Graded" ? "badge-success" : "badge-warning"}`}>{s.status}</span></td>
                  <td>{s.marks == null ? "—" : `${s.marks}/${s.max_marks}`}</td>
                  <td>{s.feedback || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
