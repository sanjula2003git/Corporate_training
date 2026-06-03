// Sidebar.jsx — written ONCE, reused on every page (this is the big win
// over Phase 1/2 where the nav was copy-pasted into 8 files).
// NavLink auto-applies an "active" class to the current route.
import { NavLink } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/students", label: "Students" },
  { to: "/trainers", label: "Trainers" },
  { to: "/courses", label: "Courses" },
  { to: "/attendance", label: "Attendance" },
  { to: "/certificates", label: "Certificates" },
  { to: "/reports", label: "Reports" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">ABC Learning</div>
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
