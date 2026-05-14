export function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="panel metric-card">
      <span className="meta-label">{label}</span>
      <strong>{value}</strong>
    </article>
  )
}
