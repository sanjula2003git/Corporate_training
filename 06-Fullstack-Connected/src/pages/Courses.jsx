// Courses.jsx — course list/add/delete, now backed by the database.
// CourseTable raises onDelete(name) (it doesn't know about ids), so here we
// look up the matching row's id and delete by id — keeping the component
// reusable and unchanged from 03.
import { useState, useEffect } from "react";
import CourseTable from "../components/CourseTable.jsx";
import { getCourses, addCourse, deleteCourse } from "../services/api.js";

export default function Courses() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", trainer: "Suresh Rao", duration: "", status: "Upcoming" });

  const load = () => getCourses().then(setRows).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const handleDelete = async (name) => {
    setError("");
    const course = rows.find((c) => c.name === name);
    if (!course) return;
    try { await deleteCourse(course.id); load(); }
    catch (e) { setError(e.message); }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.name) return;
    setError("");
    try {
      await addCourse(form);
      setForm({ name: "", trainer: "Suresh Rao", duration: "", status: "Upcoming" });
      load();
    } catch (err) { setError(err.message); }
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      {error && <p className="form-error">{error}</p>}

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
