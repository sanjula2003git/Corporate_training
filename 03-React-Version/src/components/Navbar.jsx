// Navbar.jsx — top bar. Derives its title from the current route so we don't
// hard-code it on each page. Demonstrates reading router state in a component.
import { useLocation, useNavigate } from "react-router-dom";

const titles = {
  "/dashboard": "Dashboard",
  "/students": "Student Management",
  "/trainers": "Trainer Management",
  "/courses": "Course Management",
  "/attendance": "Attendance Management",
  "/certificates": "Certificate Management",
  "/reports": "Reports Dashboard",
};

export default function Navbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  return (
    <header className="navbar">
      <h1>{titles[pathname] ?? "Training Management Portal"}</h1>
      <div className="user">
        <span>Welcome, Admin</span>
        <button className="btn btn-sm btn-secondary" onClick={() => navigate("/")}>
          Logout
        </button>
      </div>
    </header>
  );
}
