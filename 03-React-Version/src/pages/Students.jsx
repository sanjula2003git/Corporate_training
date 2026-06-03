// Students.jsx — owns student STATE. Demonstrates useState + useEffect,
// live search (derived state), add, and delete — real interactivity that
// Phase 1/2 could not do.
import { useState, useEffect } from "react";
import StudentTable from "../components/StudentTable.jsx";
import { fetchData } from "../services/mockData.js";

export default function Students() {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({ name: "", email: "", course: "React Fundamentals", status: "Active" });

  // useEffect runs after first render — simulates loading data from an API.
  useEffect(() => {
    fetchData("students").then(setRows);
  }, []);

  // Derived list — recomputed on each render, no extra state needed.
  const visible = rows.filter(
    (s) =>
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.email.toLowerCase().includes(query.toLowerCase())
  );

  const handleDelete = (id) => setRows((prev) => prev.filter((s) => s.id !== id));

  const handleAdd = (e) => {
    e.preventDefault();
    if (!form.name) return;
    const id = `STU-${String(rows.length + 1).padStart(3, "0")}`;
    setRows((prev) => [...prev, { id, ...form }]);
    setForm({ name: "", email: "", course: "React Fundamentals", status: "Active" });
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
