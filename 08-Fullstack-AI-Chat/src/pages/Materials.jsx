// Materials.jsx — course materials.
//   • Students: READ-ONLY list (only their course's materials, filtered by API).
//   • Trainers/Admins: same list + a form to add materials and delete buttons.
import { useState, useEffect } from "react";
import { getMaterials, addMaterial, deleteMaterial, getCourses, getRole } from "../services/api.js";

export default function Materials() {
  const role = getRole();
  const canManage = role === "trainer" || role === "admin";

  const [rows, setRows] = useState([]);
  const [courses, setCourses] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ course: "", title: "", kind: "Document", url: "", description: "" });

  const load = () => getMaterials().then(setRows).catch((e) => setError(e.message));
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
    if (!form.title || !form.course) return;
    setError("");
    try {
      await addMaterial(form);
      setForm((f) => ({ ...f, title: "", url: "", description: "" }));
      load();
    } catch (err) { setError(err.message); }
  };

  const handleDelete = async (id) => {
    setError("");
    try { await deleteMaterial(id); load(); }
    catch (e) { setError(e.message); }
  };

  return (
    <>
      <div className="page-head"><h2>Course Materials</h2></div>
      {error && <p className="form-error">{error}</p>}

      {rows.length === 0 && <div className="panel">No materials available yet.</div>}

      <div className="card-grid">
        {rows.map((m) => (
          <div className="card material-card" key={m.id}>
            <span className={`badge ${m.kind === "Video" ? "badge-warning" : m.kind === "Link" ? "badge-muted" : "badge-success"}`}>{m.kind}</span>
            <h3 style={{ marginTop: ".5rem" }}>{m.title}</h3>
            <p className="muted-line">{m.course}</p>
            <p style={{ fontSize: ".88rem", margin: ".5rem 0" }}>{m.description}</p>
            <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
              {m.url && <a className="btn btn-sm" href={m.url} target="_blank" rel="noreferrer">Open</a>}
              {canManage && <button className="btn btn-sm btn-danger" onClick={() => handleDelete(m.id)}>Delete</button>}
            </div>
            {m.uploaded_by && <p className="muted-line" style={{ marginTop: ".5rem" }}>by {m.uploaded_by}</p>}
          </div>
        ))}
      </div>

      {canManage && (
        <div className="panel" style={{ marginTop: "1.5rem" }}>
          <h2>Add Material</h2>
          <form className="form-grid" onSubmit={handleAdd}>
            <div className="field"><label>Course</label>
              <select value={form.course} onChange={set("course")}>
                {courses.map((c) => <option key={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field"><label>Title</label>
              <input type="text" value={form.title} onChange={set("title")} /></div>
            <div className="field"><label>Type</label>
              <select value={form.kind} onChange={set("kind")}>
                <option>Document</option><option>Video</option><option>Link</option>
              </select>
            </div>
            <div className="field"><label>URL</label>
              <input type="text" placeholder="https://…" value={form.url} onChange={set("url")} /></div>
            <div className="field"><label>Description</label>
              <input type="text" value={form.description} onChange={set("description")} /></div>
            <div className="field" style={{ justifyContent: "flex-end" }}>
              <label>&nbsp;</label><button className="btn" type="submit">Add Material</button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
