// Courses.jsx — owns course state; add + delete.
import { useState, useEffect } from "react";
import CourseTable from "../components/CourseTable.jsx";
import { fetchData } from "../services/mockData.js";

export default function Courses() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ name: "", trainer: "Suresh Rao", duration: "", status: "Upcoming" });

  useEffect(() => {
    fetchData("courses").then(setRows);
  }, []);

  const handleDelete = (name) => setRows((prev) => prev.filter((c) => c.name !== name));

  const handleAdd = (e) => {
    e.preventDefault();
    if (!form.name) return;
    setRows((prev) => [...prev, { ...form }]);
    setForm({ name: "", trainer: "Suresh Rao", duration: "", status: "Upcoming" });
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <CourseTable rows={rows} onDelete={handleDelete} />

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Add Course</h2>
        <form className="form-grid" onSubmit={handleAdd}>
          <div className="field"><label>Course Name</label>
            <input type="text" value={form.name} onChange={set("name")} /></div>
          <div className="field"><label>Trainer</label>
            <select value={form.trainer} onChange={set("trainer")}>
              <option>Suresh Rao</option><option>Anita Sharma</option><option>Priya Menon</option>
            </select>
          </div>
          <div className="field"><label>Duration</label>
            <input type="text" placeholder="e.g. 6 Weeks" value={form.duration} onChange={set("duration")} /></div>
          <div className="field"><label>Status</label>
            <select value={form.status} onChange={set("status")}>
              <option>Upcoming</option><option>Ongoing</option><option>Completed</option>
            </select>
          </div>
          <div className="field" style={{ justifyContent: "flex-end" }}>
            <label>&nbsp;</label><button className="btn" type="submit">Add Course</button>
          </div>
        </form>
      </div>
    </>
  );
}
