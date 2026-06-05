// TrainerTable.jsx — same pattern as StudentTable.
export default function TrainerTable({ rows, onDelete }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Trainer ID</th><th>Trainer Name</th><th>Expertise</th><th>Assigned Courses</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.name}</td>
              <td>{t.expertise}</td>
              <td>{t.courses}</td>
              <td>
                <button className="btn btn-sm btn-secondary">Edit</button>{" "}
                <button className="btn btn-sm btn-danger" onClick={() => onDelete(t.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
