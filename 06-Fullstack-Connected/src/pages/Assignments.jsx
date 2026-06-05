// Assignments.jsx — role-aware.
//   • Students: see the assignments for their course, submit/resubmit work
//     (typed answer + optional link), and view their marks + feedback.
//   • Trainers/Admins: create assignments, see submission counts, and expand
//     each one to review every student's submission and give marks.
import { useState, useEffect } from "react";
import AssignmentReview from "../components/AssignmentReview.jsx";
import {
  getAssignments, addAssignment, deleteAssignment, submitAssignment,
  getCourses, getRole,
} from "../services/api.js";

export default function Assignments() {
  const role = getRole();
  const isStudent = role === "student";
  const canManage = role === "trainer" || role === "admin";

  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  const load = () => getAssignments().then(setRows).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  return (
    <>
      <div className="page-head"><h2>{isStudent ? "My Assignments" : "Assignments"}</h2></div>
      {error && <p className="form-error">{error}</p>}

      {canManage && <CreateAssignment onCreated={load} setError={setError} />}

      {rows.length === 0 && <div className="panel">No assignments yet.</div>}

      {isStudent
        ? rows.map((a) => <StudentAssignment key={a.id} a={a} onSubmitted={load} />)
        : rows.map((a) => <StaffAssignment key={a.id} a={a} onChanged={load} />)}
    </>
  );
}

// ---------- STUDENT: one assignment card with a submit form ----------
function StudentAssignment({ a, onSubmitted }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState(a.my_content || "");
  const [link, setLink] = useState(a.my_link || "");
  const [error, setError] = useState("");
  const graded = a.submission_status === "Graded";

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await submitAssignment(a.id, { content, link });
      setOpen(false);
      onSubmitted();
    } catch (err) { setError(err.message); }
  };

  return (
    <div className="panel" style={{ marginBottom: "1rem" }}>
      <div className="submission-head">
        <h2 style={{ margin: 0 }}>{a.title}</h2>
        <span className={`badge ${graded ? "badge-success" : a.submission_status === "Submitted" ? "badge-warning" : "badge-muted"}`}>
          {a.submission_status}
        </span>
      </div>
      <p style={{ fontSize: ".9rem", color: "var(--color-muted)" }}>{a.description}</p>
      <p className="muted-line">Due {a.due_date || "—"} · Max marks {a.max_marks}</p>

      {graded && (
        <div className="graded-box">
          <strong>Marks: {a.my_marks}/{a.max_marks}</strong>
          {a.my_feedback && <p>Feedback: {a.my_feedback}</p>}
        </div>
      )}

      {error && <p className="form-error">{error}</p>}

      {!open && (
        <button className="btn btn-sm" onClick={() => setOpen(true)}>
          {a.submission_status === "Pending" ? "Submit Work" : "Resubmit"}
        </button>
      )}

      {open && (
        <form onSubmit={submit} style={{ marginTop: ".75rem" }}>
          <div className="field">
            <label>Your answer</label>
            <textarea rows="4" value={content} onChange={(e) => setContent(e.target.value)} />
          </div>
          <div className="field" style={{ marginTop: ".5rem" }}>
            <label>Link (optional)</label>
            <input type="text" placeholder="https://github.com/…" value={link} onChange={(e) => setLink(e.target.value)} />
          </div>
          <div style={{ marginTop: ".75rem", display: "flex", gap: ".5rem" }}>
            <button className="btn btn-sm" type="submit">Submit</button>
            <button className="btn btn-sm btn-secondary" type="button" onClick={() => setOpen(false)}>Cancel</button>
          </div>
        </form>
      )}
    </div>
  );
}

// ---------- STAFF: assignment row + expandable review panel ----------
function StaffAssignment({ a, onChanged }) {
  const [open, setOpen] = useState(false);

  const remove = async () => {
    if (!confirm(`Delete assignment "${a.title}"? This removes its submissions too.`)) return;
    try { await deleteAssignment(a.id); onChanged(); }
    catch (e) { alert(e.message); }
  };

  return (
    <div className="panel" style={{ marginBottom: "1rem" }}>
      <div className="submission-head">
        <h2 style={{ margin: 0 }}>{a.title} <span className="muted-line">· {a.course}</span></h2>
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
          {a.pending > 0
            ? <span className="badge badge-warning">{a.pending} to review</span>
            : <span className="badge badge-success">all graded</span>}
          <button className="btn btn-sm btn-secondary" onClick={() => setOpen((o) => !o)}>
            {open ? "Hide" : `Review (${a.submission_count})`}
          </button>
          <button className="btn btn-sm btn-danger" onClick={remove}>Delete</button>
        </div>
      </div>
      <p style={{ fontSize: ".9rem", color: "var(--color-muted)" }}>{a.description}</p>
      <p className="muted-line">Due {a.due_date || "—"} · Max marks {a.max_marks} · {a.graded_count}/{a.submission_count} graded</p>
      {open && <AssignmentReview assignmentId={a.id} maxMarks={a.max_marks} />}
    </div>
  );
}

// ---------- STAFF: create-assignment form ----------
function CreateAssignment({ onCreated, setError }) {
  const [courses, setCourses] = useState([]);
  const [form, setForm] = useState({ course: "", title: "", description: "", due_date: "", max_marks: 100 });

  useEffect(() => {
    getCourses().then((c) => {
      setCourses(c);
      if (c.length) setForm((f) => ({ ...f, course: c[0].name }));
    }).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.title || !form.course) return;
    setError("");
    try {
      await addAssignment({ ...form, max_marks: Number(form.max_marks) });
      setForm((f) => ({ ...f, title: "", description: "", due_date: "" }));
      onCreated();
    } catch (err) { setError(err.message); }
  };

  return (
    <div className="panel" style={{ marginBottom: "1.5rem" }}>
      <h2>Create Assignment</h2>
      <form className="form-grid" onSubmit={submit}>
        <div className="field"><label>Course</label>
          <select value={form.course} onChange={set("course")}>
            {courses.map((c) => <option key={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="field"><label>Title</label>
          <input type="text" value={form.title} onChange={set("title")} /></div>
        <div className="field"><label>Due Date</label>
          <input type="date" value={form.due_date} onChange={set("due_date")} /></div>
        <div className="field"><label>Max Marks</label>
          <input type="number" min="1" value={form.max_marks} onChange={set("max_marks")} /></div>
        <div className="field" style={{ gridColumn: "1 / -1" }}><label>Description</label>
          <input type="text" value={form.description} onChange={set("description")} /></div>
        <div className="field" style={{ justifyContent: "flex-end" }}>
          <label>&nbsp;</label><button className="btn" type="submit">Create</button>
        </div>
      </form>
    </div>
  );
}
