// Students.jsx — same UI as 03, but now backed by the REAL database.
//   • load   → GET    /api/students   (SELECT)
//   • add    → POST   /api/students   (INSERT)  → then reload from DB
//   • delete → DELETE /api/students/ID (DELETE) → then reload from DB
// After add/delete we re-fetch so the table always mirrors the database
// (and the new student shows the backend-generated id, e.g. STU-007).
import { useState, useEffect } from "react";
import StudentTable from "../components/StudentTable.jsx";
import { getStudents, addStudent, deleteStudent } from "../services/api.js";

export default function Students() {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [created, setCreated] = useState(null); // login auto-made for the new student
  const [form, setForm] = useState({ name: "", email: "", course: "React Fundamentals", status: "Active" });

  // Reusable loader — call it on mount and after every change.
  const load = () => getStudents().then(setRows).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  // Live search — derived from state, recomputed each render.
  const visible = rows.filter(
    (s) =>
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.email.toLowerCase().includes(query.toLowerCase())
  );

  const handleDelete = async (id) => {
    setError("");
    try {
      await deleteStudent(id); // removes the row from the database
      load();                  // reload so the table reflects the DB
    } catch (e) {
      setError(e.message);     // e.g. only admins can delete
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.name) return;
    setError("");
    try {
      const res = await addStudent(form);  // INSERT student + auto-create login
      setCreated(res.login);               // { username, password } to share
      setForm({ name: "", email: "", course: "React Fundamentals", status: "Active" });
      load();                              // reload → new STU-00x appears
    } catch (err) {
      setError(err.message);
    }
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <div className="toolbar">
        <div className="search">
          <input
            type="search"
            placeholder="Search student..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}
      {created && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <span className="badge badge-success">Login created</span>{" "}
          Username <b>{created.username}</b> · Password <b>{created.password}</b>
          <span className="muted-line"> — share these so the student can sign in.</span>
        </div>
      )}

      <StudentTable rows={visible} onDelete={handleDelete} />

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Add Student</h2>
        <form className="form-grid" onSubmit={handleAdd}>
          <div className="field"><label>Student Name</label>
            <input type="text" value={form.name} onChange={set("name")} /></div>
          <div className="field"><label>Email</label>
            <input type="email" value={form.email} onChange={set("email")} /></div>
          <div className="field"><label>Course</label>
            <select value={form.course} onChange={set("course")}>
              <option>React Fundamentals</option><option>Java Backend</option><option>Python Basics</option>
            </select>
          </div>
          <div className="field"><label>Status</label>
            <select value={form.status} onChange={set("status")}>
              <option>Active</option><option>Inactive</option>
            </select>
          </div>
          <div className="field" style={{ justifyContent: "flex-end" }}>
            <label>&nbsp;</label><button className="btn" type="submit">Add Student</button>
          </div>
        </form>
      </div>
    </>
  );
}
