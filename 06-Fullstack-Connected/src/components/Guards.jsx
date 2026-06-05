// Guards.jsx — tiny route protectors.
//   • RequireAuth: no token? → bounce to the login page.
//   • RequireRole: logged in but wrong role? → bounce to your own dashboard.
// (The backend ALSO enforces this — these just keep the UI tidy so people
//  don't see buttons/pages that aren't theirs.)
import { Navigate } from "react-router-dom";
import { getToken, getRole } from "../services/api.js";

export function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/" replace />;
}

export function RequireRole({ roles, children }) {
  if (!getToken()) return <Navigate to="/" replace />;
  return roles.includes(getRole()) ? children : <Navigate to="/dashboard" replace />;
}
