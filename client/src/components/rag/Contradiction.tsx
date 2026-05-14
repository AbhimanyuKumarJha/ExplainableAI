export function Contradiction({ title, body }: { title: string; body: string }) {
  return (
    <div className="contradiction">
      <span>{title}</span>
      <p>{body}</p>
    </div>
  )
}
