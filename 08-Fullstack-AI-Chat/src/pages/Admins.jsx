// Admins.jsx — admin-only. Lists all logins and lets an admin add ANOTHER
// admin (who then has the same powers). Reads /api/users, posts /api/admins.
import { useState, useEffect } from "react";
import { getUsers, addAdmin } from "../services/api.js";

export default function Admins() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({ name: "", username: "", password: "" });

  const load = () => getUsers().then(setUsers).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.name || !form.username || !form.password) return;
    setError(""); setMessage("");
    try {
      await addAdmin(form);
      setMessage(`Admin "${form.username}" created ✓`);
      setForm({ name: "", username: "", password: "" });
      load();
    } catch (err) { setError(err.message); }
  };

  const admins = users.filter((u) => u.role === "admin");

  return (
    <>
      <div className="page-head"><h2>Admins &amp; Accounts</h2></div>
      {error && <p className="form-error">{error}</p>}
      {message && <div className="panel" style={{ marginBottom: "1rem" }}><span className="badge badge-success">{message}</span></div>}

      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <h2>Add Another Admin</h2>
        <p className="muted-line">A new admin can add courses, students and trainers, and sees the full dashboard.</p>
        <form className="form-grid" onSubmit={handleAdd}>
          <div className="field"><label>Full Name</label>
            <input type="text" value={form.name} onChange={set("name")} /></div>
          <div className="field"><label>Username</label>
            <input type="text" value={form.username} onChange={set("username")} /></div>
          <div className="field"><label>Password</label>
            <input type="text" value={form.password} onChange={set("password")} /></div>
          <div className="field" style={{ justifyContent: "flex-end" }}>
            <label>&nbsp;</label><button className="btn" type="submit">Add Admin</button>
          </div>
        </form>
      </div>

      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <h2>Admins ({admins.length})</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Username</th><th>Name</th><th>Role</th></tr></thead>
            <tbody>
              {admins.map((u) => (
                <tr key={u.username}><td>{u.username}</td><td>{u.name}</td><td><span className="badge badge-success">{u.role}</span></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>All Accounts ({users.length})</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Username</th><th>Name</th><th>Role</th><th>Linked Record</th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.username}>
                  <td>{u.username}</td>
                  <td>{u.name}</td>
                  <td><span className={`badge ${u.role === "admin" ? "badge-success" : u.role === "trainer" ? "badge-warning" : "badge-muted"}`}>{u.role}</span></td>
                  <td>{u.ref_id || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
