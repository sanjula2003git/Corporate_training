// AssignmentReview.jsx — staff view of EVERY student's submission for one
// assignment, shown separately per student, each with a grade + feedback form.
// Used by trainers/admins inside the Assignments page.
import { useState, useEffect } from "react";
import { getSubmissions, gradeSubmission } from "../services/api.js";

function GradeRow({ sub, maxMarks, onGraded }) {
  const [marks, setMarks] = useState(sub.marks ?? "");
  const [feedback, setFeedback] = useState(sub.feedback || "");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const save = async () => {
    setMsg(""); setError("");
    try {
      await gradeSubmission(sub.id, { marks: Number(marks), feedback });
      setMsg("Saved ✓");
      onGraded();
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="submission-row">
      <div className="submission-head">
        <strong>{sub.student_name}</strong>
        <span className={`badge ${sub.status === "Graded" ? "badge-success" : "badge-warning"}`}>{sub.status}</span>
      </div>
      {sub.content && <p className="submission-content">{sub.content}</p>}
      {sub.link && <a href={sub.link} target="_blank" rel="noreferrer">{sub.link}</a>}
      <div className="grade-form">
        <input
          type="number" min="0" max={maxMarks} value={marks}
          placeholder={`/ ${maxMarks}`} onChange={(e) => setMarks(e.target.value)}
          style={{ width: 90 }}
        />
        <input
          type="text" value={feedback} placeholder="Feedback…"
          onChange={(e) => setFeedback(e.target.value)} style={{ flex: 1 }}
        />
        <button className="btn btn-sm" onClick={save} disabled={marks === ""}>Save Marks</button>
        {msg && <span className="badge badge-success">{msg}</span>}
        {error && <span className="form-error" style={{ margin: 0, padding: ".2rem .5rem" }}>{error}</span>}
      </div>
    </div>
  );
}

export default function AssignmentReview({ assignmentId, maxMarks }) {
  const [subs, setSubs] = useState([]);
  const [error, setError] = useState("");

  const load = () => getSubmissions(assignmentId).then(setSubs).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [assignmentId]);

  if (error) return <p className="form-error">{error}</p>;
  if (subs.length === 0) return <p className="muted-line">No submissions yet.</p>;

  return (
    <div className="review-list">
      {subs.map((s) => (
        <GradeRow key={s.id} sub={s} maxMarks={maxMarks} onGraded={load} />
      ))}
    </div>
  );
}
