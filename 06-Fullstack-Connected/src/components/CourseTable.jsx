// CourseTable.jsx — renders courses; maps status → coloured badge.
export default function CourseTable({ rows, onDelete }) {
  const badge = (status) =>
    status === "Completed" ? "badge-success" : status === "Ongoing" ? "badge-warning" : "badge-muted";

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Course Name</th><th>Trainer</th><th>Duration</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.name}>
              <td>{c.name}</td>
              <td>{c.trainer}</td>
              <td>{c.duration}</td>
              <td><span className={`badge ${badge(c.status)}`}>{c.status}</span></td>
              <td>
                <button className="btn btn-sm btn-secondary">Edit</button>{" "}
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(c.name)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
