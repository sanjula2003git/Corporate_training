// AttendanceForm.jsx — a CONTROLLED form, now wired to the database.
//   • students + courses are loaded from the API (not mock arrays)
//   • Save → POST /api/attendance, which INSERTs an attendance row and
//     stores how many students were present.
import { useState, useEffect } from "react";
import { getStudents, getCourses, saveAttendance } from "../services/api.js";

export default function AttendanceForm() {
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [course, setCourse] = useState("");
  const [date, setDate] = useState("");
  const [present, setPresent] = useState({}); // { "STU-001": true, ... }
  const [savedMsg, setSavedMsg] = useState("");
  const [error, setError] = useState("");

  // Load the dropdown + checkbox data from the backend on mount.
  useEffect(() => {
    Promise.all([getStudents(), getCourses()])
      .then(([studs, crs]) => {
        setStudents(studs);
        setCourses(crs);
        if (crs.length) setCourse(crs[0].name);
        // Everyone defaults to present.
        setPresent(Object.fromEntries(studs.map((s) => [s.id, true])));
      })
      .catch((e) => setError(e.message));
  }, []);

  const toggle = (id) => setPresent((prev) => ({ ...prev, [id]: !prev[id] }));

  // Only the students enrolled in the selected course can be marked — the
  // backend marks this whole roster (ticked = Present, rest = Absent).
  const roster = students.filter((s) => s.course === course);

  const handleSave = async (e) => {
    e.preventDefault();
    setSavedMsg(""); setError("");
    // Collect the ids of everyone in this course ticked "present".
    const presentIds = roster.filter((s) => present[s.id]).map((s) => s.id);
    try {
      const res = await saveAttendance({ course, date, present: presentIds });
      setSavedMsg(`Saved ${res.present_count} present for ${res.course}${date ? ` on ${date}` : ""} ✓`);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="panel">
      <h2>Mark Attendance</h2>
      {error && <p className="form-error">{error}</p>}
      <form onSubmit={handleSave}>
        <div className="form-grid" style={{ marginBottom: "1rem" }}>
          <div className="field">
            <label>Course</label>
            <select value={course} onChange={(e) => setCourse(e.target.value)}>
              {courses.map((c) => (
                <option key={c.id}>{c.name}</option>
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
              {roster.length === 0 && (
                <tr><td colSpan="2">No students enrolled in this course.</td></tr>
              )}
              {roster.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td>
                    <input
                      type="checkbox"
                      checked={present[s.id] || false}
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
          {savedMsg && <span className="badge badge-success">{savedMsg}</span>}
        </div>
      </form>
    </div>
  );
}
