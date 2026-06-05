// ReportsPanel.jsx — renders the per-course completion table from props.
export default function ReportsPanel({ byCourse }) {
  return (
    <div className="panel">
      <h2>Completion by Course</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Course</th><th>Enrolled</th><th>Completed</th><th>Completion Rate</th></tr>
          </thead>
          <tbody>
            {byCourse.map((r) => (
              <tr key={r.course}>
                <td>{r.course}</td>
                <td>{r.enrolled}</td>
                <td>{r.completed}</td>
                <td>{r.rate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
