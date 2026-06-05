// =====================================================================
// App.jsx — central route table (React Router) with ROLE-BASED access.
// The Login page renders standalone; every other page renders INSIDE the
// shared <Layout> (Sidebar + Navbar). Routes are wrapped in guards so each
// role only reaches the pages meant for it (the backend enforces this too).
// =====================================================================
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import { RequireAuth, RequireRole } from "./components/Guards.jsx";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Students from "./pages/Students.jsx";
import Trainers from "./pages/Trainers.jsx";
import Courses from "./pages/Courses.jsx";
import Admins from "./pages/Admins.jsx";
import Attendance from "./pages/Attendance.jsx";
import Certificates from "./pages/Certificates.jsx";
import Reports from "./pages/Reports.jsx";
import Materials from "./pages/Materials.jsx";
import Assignments from "./pages/Assignments.jsx";
import Classes from "./pages/Classes.jsx";
import MyProgress from "./pages/MyProgress.jsx";
import Messages from "./pages/Messages.jsx";

// Roles that may add/update/delete people & courses.
const ADMIN = ["admin"];
const STAFF = ["admin", "trainer"];

export default function App() {
  return (
    <Routes>
      {/* Standalone login (no sidebar) */}
      <Route path="/" element={<Login />} />

      {/* All app pages require a valid login and share the Layout */}
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        {/* Everyone (role-aware page renders the right view) */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/assignments" element={<Assignments />} />
        <Route path="/classes" element={<Classes />} />

        {/* Student-only */}
        <Route path="/progress" element={<RequireRole roles={["student"]}><MyProgress /></RequireRole>} />

        {/* Staff (trainer + admin) */}
        <Route path="/attendance" element={<RequireRole roles={STAFF}><Attendance /></RequireRole>} />
        <Route path="/reports" element={<RequireRole roles={STAFF}><Reports /></RequireRole>} />
        <Route path="/certificates" element={<RequireRole roles={STAFF}><Certificates /></RequireRole>} />

        {/* Admin-only */}
        <Route path="/students" element={<RequireRole roles={ADMIN}><Students /></RequireRole>} />
        <Route path="/trainers" element={<RequireRole roles={ADMIN}><Trainers /></RequireRole>} />
        <Route path="/courses" element={<RequireRole roles={ADMIN}><Courses /></RequireRole>} />
        <Route path="/admins" element={<RequireRole roles={ADMIN}><Admins /></RequireRole>} />
        <Route path="/messages" element={<RequireRole roles={ADMIN}><Messages /></RequireRole>} />
      </Route>

      {/* Unknown URLs → back to login */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
