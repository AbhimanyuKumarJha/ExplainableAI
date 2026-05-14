import type { RecentScan } from '../../types'
import { VerdictChip } from '../ui/VerdictChip'

export function RecentScanTable({ scans }: { scans: RecentScan[] }) {
  return (
    <div className="scan-table">
      {scans.map((scan) => (
        <div key={scan.id} className="scan-row">
          <div>
            <strong>{scan.title}</strong>
            <span>{scan.source}</span>
          </div>
          <VerdictChip verdict={scan.verdict} confidence={scan.confidence} compact />
          <time>{scan.time}</time>
        </div>
      ))}
    </div>
  )
}
