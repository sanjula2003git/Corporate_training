// StudentTable.jsx — renders the student list and raises events upward.
// It does NOT own the data; the page owns state and passes an onDelete
// callback. This "lift state up" pattern keeps the table reusable.
export default function StudentTable({ rows, onDelete }) {
  if (rows.length === 0) {
    return <div className="panel">No students match your search.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Student ID</th><th>Student Name</th><th>Email</th>
            <th>Course</th><th>Status</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={s.id}>
              <td>{s.id}</td>
              <td>{s.name}</td>
              <td>{s.email}</td>
              <td>{s.course}</td>
              <td>
                <span className={`badge ${s.status === "Active" ? "badge-success" : "badge-muted"}`}>
                  {s.status}
                </span>
              </td>
              <td>
                <button className="btn btn-sm btn-secondary">Edit</button>{" "}
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(s.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
