import type { ReactNode } from 'react'

type PageHeaderProps = {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div>
        <span className="meta-label">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {action ? <div className="page-action">{action}</div> : null}
    </div>
  )
}
