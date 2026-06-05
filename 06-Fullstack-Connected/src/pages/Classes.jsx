// Classes.jsx — online classes (Google Meet links).
//   • Students: see classes for their course and click "Join Class".
//   • Trainers/Admins: schedule a class (paste a Meet link) and delete classes.
import { useState, useEffect } from "react";
import { getClasses, addClass, deleteClass, getCourses, getRole } from "../services/api.js";

export default function Classes() {
  const role = getRole();
  const canManage = role === "trainer" || role === "admin";

  const [rows, setRows] = useState([]);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ course: "", title: "", scheduled_at: "", meet_link: "" });

  const load = () => getClasses().then(setRows).catch((e) => setError(e.message));
  useEffect(() => {
    load();
    if (canManage) getCourses().then((c) => {
      setCourses(c);
      if (c.length) setForm((f) => ({ ...f, course: c[0].name }));
    }).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.title || !form.course || !form.meet_link) return;
    setError("");
    try {
      await addClass(form);
      setForm((f) => ({ ...f, title: "", scheduled_at: "", meet_link: "" }));
      load();
    } catch (err) { setError(err.message); }
  };

  const handleDelete = async (id) => {
    setError("");
    try { await deleteClass(id); load(); }
    catch (e) { setError(e.message); }
  };

  return (
    <>
      <div className="page-head"><h2>Online Classes</h2></div>
      {error && <p className="form-error">{error}</p>}

      {rows.length === 0 && <div className="panel">No classes scheduled.</div>}

      <div className="card-grid">
        {rows.map((c) => (
          <div className="card" key={c.id}>
            <span className="badge badge-muted">{c.course}</span>
            <h3 style={{ marginTop: ".5rem" }}>{c.title}</h3>
            <p className="muted-line">🕒 {c.scheduled_at || "TBD"}</p>
            <div style={{ display: "flex", gap: ".5rem", marginTop: ".5rem" }}>
              <a className="btn btn-sm" href={c.meet_link} target="_blank" rel="noreferrer">Join Class</a>
              {canManage && <button className="btn btn-sm btn-danger" onClick={() => handleDelete(c.id)}>Delete</button>}
            </div>
            {c.created_by && <p className="muted-line" style={{ marginTop: ".5rem" }}>by {c.created_by}</p>}
          </div>
        ))}
      </div>

      {canManage && (
        <div className="panel" style={{ marginTop: "1.5rem" }}>
          <h2>Schedule a Class</h2>
          <form className="form-grid" onSubmit={handleAdd}>
            <div className="field"><label>Course</label>
              <select value={form.course} onChange={set("course")}>
                {courses.map((c) => <option key={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field"><label>Title</label>
              <input type="text" placeholder="Live: Topic" value={form.title} onChange={set("title")} /></div>
            <div className="field"><label>When</label>
              <input type="text" placeholder="2026-06-12 10:00" value={form.scheduled_at} onChange={set("scheduled_at")} /></div>
            <div className="field"><label>Google Meet Link</label>
              <input type="text" placeholder="https://meet.google.com/…" value={form.meet_link} onChange={set("meet_link")} /></div>
            <div className="field" style={{ justifyContent: "flex-end" }}>
              <label>&nbsp;</label><button className="btn" type="submit">Schedule</button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
