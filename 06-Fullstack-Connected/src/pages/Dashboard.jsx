// Dashboard.jsx — ROLE DISPATCHER.
// One URL (/dashboard), three different views depending on who logged in.
// This is the heart of "separate portals for students, trainers and admins".
import { getRole } from "../services/api.js";
import StudentDashboard from "../components/StudentDashboard.jsx";
import TrainerDashboard from "../components/TrainerDashboard.jsx";
import AdminDashboard from "../components/AdminDashboard.jsx";

export default function Dashboard() {
  const role = getRole();
  if (role === "student") return <StudentDashboard />;
  if (role === "trainer") return <TrainerDashboard />;
  if (role === "admin") return <AdminDashboard />;
  return <div className="panel">Unknown role — please log in again.</div>;
}
