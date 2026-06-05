// CertificateList.jsx — list with per-row action buttons. "Generate" is
// disabled until the course is Completed (logic lives in the component).
export default function CertificateList({ rows, onGenerate }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr><th>Student Name</th><th>Course Name</th><th>Completion Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {rows.map((c, i) => {
            const ready = c.status === "Completed";
            return (
              <tr key={i}>
                <td>{c.student}</td>
                <td>{c.course}</td>
                <td>
                  <span className={`badge ${ready ? "badge-success" : "badge-warning"}`}>
                    {c.status}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-sm"
                    disabled={!ready}
                    onClick={() => onGenerate(c)}
                  >
                    Generate Certificate
                  </button>{" "}
                  <button className="btn btn-sm btn-secondary" disabled={!ready}>
                    Download
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
