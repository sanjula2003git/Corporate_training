// Dashboard.jsx — composes DashboardCard + activity panel + chart.
import DashboardCard from "../components/DashboardCard.jsx";
import { dashboardStats, recentActivities, attendanceOverview } from "../services/mockData.js";

export default function Dashboard() {
  return (
    <>
      <section className="card-grid">
        <DashboardCard title="Total Students" value={dashboardStats.totalStudents} />
        <DashboardCard title="Total Trainers" value={dashboardStats.totalTrainers} />
        <DashboardCard title="Total Courses" value={dashboardStats.totalCourses} />
        <DashboardCard title="Average Attendance" value={dashboardStats.avgAttendance} />
      </section>

      <section className="panel-grid">
        <div className="panel">
          <h2>Recent Activities</h2>
          <ul className="activity-list">
            {recentActivities.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Attendance Overview</h2>
          <div className="chart">
            {attendanceOverview.map((d) => (
              <div key={d.day} className="bar" style={{ height: `${d.value}%` }}>
                <span>{d.day}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
