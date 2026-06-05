// Reports.jsx — stats now come from GET /api/reports, which the backend
// computes from real database queries (e.g. completion rate from certificates).
import { useState, useEffect } from "react";
import DashboardCard from "../components/DashboardCard.jsx";
import ReportsPanel from "../components/ReportsPanel.jsx";
import { getReports } from "../services/api.js";

export default function Reports() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getReports().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="panel form-error">{error}</div>;
  if (!stats) return <div className="panel">Loading reports…</div>;

  return (
    <>
      <section className="card-grid">
        <DashboardCard title="Total Students" value={stats.totalStudents} />
        <DashboardCard title="Course Completion Rate" value={stats.completionRate} />
        <DashboardCard title="Avg Attendance" value={stats.avgAttendance} />
        <DashboardCard title="Certificates Issued" value={stats.certificatesIssued} />
      </section>

      <ReportsPanel byCourse={stats.byCourse} />
    </>
  );
}
