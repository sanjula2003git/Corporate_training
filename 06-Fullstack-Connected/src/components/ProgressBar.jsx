// ProgressBar.jsx — a tiny reusable bar for percentages (attendance, progress).
// Colours by value: red <50, amber <75, green otherwise.
export default function ProgressBar({ value }) {
  const v = Math.max(0, Math.min(100, value || 0));
  const tone = v < 50 ? "danger" : v < 75 ? "warning" : "success";
  return (
    <div className="progress" title={`${v}%`}>
      <div className={`progress-bar progress-${tone}`} style={{ width: `${v}%` }}>
        {v}%
      </div>
    </div>
  );
}
