// Sidebar.jsx — written ONCE, reused on every page. The link list is now
// chosen by the logged-in user's ROLE, so students, trainers and admins each
// see their own menu (the matching pages are guarded in App.jsx too).
import { NavLink } from "react-router-dom";
import { getRole } from "../services/api.js";

// Links available to each role, in display order.
const LINKS_BY_ROLE = {
  student: [
    { to: "/dashboard", label: "My Dashboard" },
    { to: "/materials", label: "Course Materials" },
    { to: "/assignments", label: "My Assignments" },
    { to: "/classes", label: "Online Classes" },
    { to: "/progress", label: "My Progress" },
  ],
  trainer: [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/materials", label: "Materials" },
    { to: "/assignments", label: "Assignments" },
    { to: "/classes", label: "Online Classes" },
    { to: "/attendance", label: "Attendance" },
    { to: "/certificates", label: "Certificates" },
    { to: "/reports", label: "Reports" },
  ],
  admin: [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/students", label: "Students" },
    { to: "/trainers", label: "Trainers" },
    { to: "/courses", label: "Courses" },
    { to: "/admins", label: "Admins" },
    { to: "/messages", label: "AI Chat Logs" },
    { to: "/materials", label: "Materials" },
    { to: "/assignments", label: "Assignments" },
    { to: "/classes", label: "Online Classes" },
    { to: "/attendance", label: "Attendance" },
    { to: "/certificates", label: "Certificates" },
    { to: "/reports", label: "Reports" },
  ],
};

export default function Sidebar() {
  const role = getRole();
  const links = LINKS_BY_ROLE[role] || LINKS_BY_ROLE.student;

  return (
    <aside className="sidebar">
      <div className="brand">
        ABC Learning
        {role && <span className="role-chip">{role}</span>}
      </div>
      <nav>
        <ul>
          {links.map((l) => (
            <li key={l.to}>
              <NavLink
                to={l.to}
                className={({ isActive }) => (isActive ? "active" : "")}
              >
                {l.label}
              </NavLink>
            </li>
          ))}
          <li>
            <NavLink to="/">Logout</NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
