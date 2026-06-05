// Navbar.jsx — top bar. Title is derived from the current route.
// Now it shows the REAL logged-in user (from the token) and a live-connection
// badge, and Logout clears the saved token before returning to the login page.
import { useLocation, useNavigate } from "react-router-dom";
import { getUser, logout } from "../services/api.js";

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
  const user = getUser();

  const handleLogout = () => {
    logout();          // clear the saved token
    navigate("/");     // back to login
  };

  return (
    <header className="navbar">
      <h1>{titles[pathname] ?? "Training Management Portal"}</h1>
      <div className="user">
        <span className="live-badge">🤖 AI Chat · Phase 2</span>
        <span>Welcome, {user.name}{user.role ? ` (${user.role})` : ""}</span>
        <button className="btn btn-sm btn-secondary" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
