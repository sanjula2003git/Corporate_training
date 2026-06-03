// Reports.jsx — reuses DashboardCard + ReportsPanel components.
import DashboardCard from "../components/DashboardCard.jsx";
import ReportsPanel from "../components/ReportsPanel.jsx";
import { reportStats } from "../services/mockData.js";

export default function Reports() {
  return (
    <>
      <section className="card-grid">
        <DashboardCard title="Total Students" value={reportStats.totalStudents} />
        <DashboardCard title="Course Completion Rate" value={reportStats.completionRate} />
        <DashboardCard title="Avg Attendance" value={reportStats.avgAttendance} />
        <DashboardCard title="Certificates Issued" value={reportStats.certificatesIssued} />
      </section>

      <ReportsPanel byCourse={reportStats.byCourse} />
    </>
  );
}
