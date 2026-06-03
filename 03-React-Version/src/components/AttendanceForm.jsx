// AttendanceForm.jsx — a CONTROLLED form. Every input's value lives in
// React state (useState), so the UI and data are always in sync.
import { useState } from "react";
import { courses, students } from "../services/mockData.js";

export default function AttendanceForm() {
  const [course, setCourse] = useState(courses[0].name);
  const [date, setDate] = useState("");
  // present = { "STU-001": true, ... }
  const [present, setPresent] = useState(
    Object.fromEntries(students.map((s) => [s.id, true]))
  );
  const [saved, setSaved] = useState(false);

  const toggle = (id) =>
    setPresent((prev) => ({ ...prev, [id]: !prev[id] }));

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    // In a real app: POST { course, date, present } to the backend.
  };

  return (
    <div className="panel">
      <h2>Mark Attendance</h2>
      <form onSubmit={handleSave}>
        <div className="form-grid" style={{ marginBottom: "1rem" }}>
          <div className="field">
            <label>Course</label>
            <select value={course} onChange={(e) => setCourse(e.target.value)}>
              {courses.map((c) => (
                <option key={c.name}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead><tr><th>Student Name</th><th>Present</th></tr></thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>
                    <input
                      type="checkbox"
                      checked={present[s.id]}
                      onChange={() => toggle(s.id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: "1rem", display: "flex", gap: "1rem", alignItems: "center" }}>
          <button className="btn" type="submit">Save Attendance</button>
          {saved && (
            <span className="badge badge-success">
              Saved for {course}{date ? ` on ${date}` : ""} ✓
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
