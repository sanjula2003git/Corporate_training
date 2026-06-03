// DashboardCard.jsx — a tiny REUSABLE component.
// Receives data through "props" and just renders it. Used 4x on the
// dashboard and 4x on reports with zero duplication.
export default function DashboardCard({ title, value }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="value">{value}</div>
    </div>
  );
}
