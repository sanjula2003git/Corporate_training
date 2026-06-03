// =====================================================================
// App.jsx — central route table (React Router).
// The Login page renders standalone; every other page renders INSIDE the
// shared <Layout> (Sidebar + Navbar), so that chrome is written ONCE.
// =====================================================================
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Students from "./pages/Students.jsx";
import Trainers from "./pages/Trainers.jsx";
import Courses from "./pages/Courses.jsx";
import Attendance from "./pages/Attendance.jsx";
import Certificates from "./pages/Certificates.jsx";
import Reports from "./pages/Reports.jsx";

export default function App() {
  return (
    <Routes>
      {/* Standalone login (no sidebar) */}
      <Route path="/" element={<Login />} />

      {/* App pages share the Layout via nested routes */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/students" element={<Students />} />
        <Route path="/trainers" element={<Trainers />} />
        <Route path="/courses" element={<Courses />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/certificates" element={<Certificates />} />
        <Route path="/reports" element={<Reports />} />
      </Route>

      {/* Unknown URLs → back to login */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
