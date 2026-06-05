// AdminDashboard.jsx — the WHOLE-ORG view (both admins get this): totals,
// every student's attendance & marks, every trainer, and per-course progress.
// Data comes from GET /api/dashboard/admin.
import { useState, useEffect } from "react";
import DashboardCard from "./DashboardCard.jsx";
import ProgressBar from "./ProgressBar.jsx";
import { getAdminDashboard } from "../services/api.js";

export default function AdminDashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminDashboard().then(setD).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="panel form-error">{error}</div>;
  if (!d) return <div className="panel">Loading dashboard…</div>;

  return (
    <>
      <section className="card-grid">
        <DashboardCard title="Total Students" value={d.totalStudents} />
        <DashboardCard title="Total Trainers" value={d.totalTrainers} />
        <DashboardCard title="Total Courses" value={d.totalCourses} />
        <DashboardCard title="Avg Attendance" value={`${d.avgAttendance}%`} />
      </section>

      <div className="panel" style={{ marginBottom: "1.25rem" }}>
        <h2>Course Progress</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Course</th><th>Trainer</th><th>Enrolled</th><th>Avg Attendance</th><th>Avg Marks</th><th>Status</th></tr>
            </thead>
            <tbody>
              {d.courses.map((c) => (
                <tr key={c.course}>
                  <td>{c.course}</td>
                  <td>{c.trainer}</td>
                  <td>{c.enrolled}</td>
                  <td style={{ minWidth: 140 }}><ProgressBar value={c.avgAttendance} /></td>
                  <td>{c.avgMarks == null ? "—" : c.avgMarks}</td>
                  <td><span className={`badge ${c.status === "Completed" ? "badge-success" : c.status === "Ongoing" ? "badge-warning" : "badge-muted"}`}>{c.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: "1.25rem" }}>
        <h2>Every Student — Attendance &amp; Progress</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>Student</th><th>Course</th><th>Attendance</th><th>Assignments</th><th>Avg Marks</th></tr>
            </thead>
            <tbody>
              {d.students.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.name}</td>
                  <td>{s.course}</td>
                  <td style={{ minWidth: 140 }}><ProgressBar value={s.attendancePct} /></td>
                  <td>{s.submitted}/{s.assignmentsTotal}</td>
                  <td>{s.avgMarks == null ? "—" : s.avgMarks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Trainers</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>Trainer</th><th>Expertise</th><th>Courses</th></tr>
            </thead>
            <tbody>
              {d.trainers.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.name}</td>
                  <td>{t.expertise}</td>
                  <td>{t.courses}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
