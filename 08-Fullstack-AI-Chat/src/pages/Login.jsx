// Login.jsx — REAL authentication against the backend.
// Unlike 03-React-Version (which accepted anything), this calls
// POST /api/auth/login. Only valid database users get in, and we keep the
// returned token so later requests are allowed.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/api.js";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password); // talks to the backend
      navigate("/dashboard");          // only reached if login succeeded
    } catch (err) {
      setError(err.message);           // e.g. "Incorrect username or password"
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>ABC Learning Solutions</h1>
        <p className="sub">Training Management Portal · Live Database</p>

        <div className="field">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            required
          />
        </div>
        <div className="field">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>

        {error && <p className="form-error">{error}</p>}

        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Login"}
        </button>

        <p className="login-hint">
          Demo logins —<br />
          Admin: <b>admin / admin123</b><br />
          Trainer: <b>suresh / trainer123</b><br />
          Student: <b>ravi / student123</b>
        </p>
      </form>
    </div>
  );
}
