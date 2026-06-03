// Trainers.jsx — owns trainer state; add + delete.
import { useState, useEffect } from "react";
import TrainerTable from "../components/TrainerTable.jsx";
import { fetchData } from "../services/mockData.js";

export default function Trainers() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ name: "", expertise: "", courses: "" });

  useEffect(() => {
    fetchData("trainers").then(setRows);
  }, []);

  const handleDelete = (id) => setRows((prev) => prev.filter((t) => t.id !== id));

  const handleAdd = (e) => {
    e.preventDefault();
    if (!form.name) return;
    const id = `TRN-${String(rows.length + 1).padStart(3, "0")}`;
    setRows((prev) => [...prev, { id, ...form }]);
    setForm({ name: "", expertise: "", courses: "" });
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <div className="toolbar">
        <h2 style={{ fontSize: "1rem", color: "var(--color-muted)" }}>All Trainers</h2>
      </div>

      <TrainerTable rows={rows} onDelete={handleDelete} />

      <div className="panel" style={{ marginTop: "1.5rem" }}>
        <h2>Add Trainer</h2>
        <form className="form-grid" onSubmit={handleAdd}>
          <div className="field"><label>Trainer Name</label>
            <input type="text" value={form.name} onChange={set("name")} /></div>
          <div className="field"><label>Expertise</label>
            <input type="text" value={form.expertise} onChange={set("expertise")} /></div>
          <div className="field"><label>Assigned Courses</label>
            <input type="text" value={form.courses} onChange={set("courses")} /></div>
          <div className="field" style={{ justifyContent: "flex-end" }}>
            <label>&nbsp;</label><button className="btn" type="submit">Add Trainer</button>
          </div>
        </form>
      </div>
    </>
  );
}
