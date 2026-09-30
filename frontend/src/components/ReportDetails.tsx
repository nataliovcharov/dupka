import { useEffect, useState } from 'react'

import { reportPhotoUrl } from '../api'
import type { ReportProperties, Severity } from '../types'

const DAMAGE_LABELS: Record<string, string> = {
  D40: 'Pothole',
  D20: 'Alligator cracking',
  D10: 'Transverse crack',
  D00: 'Longitudinal crack',
}

const SEVERITY_LABELS: Record<Severity, string> = {
  high: 'High severity',
  medium: 'Medium severity',
  low: 'Low severity',
}

const dateFormat = new Intl.DateTimeFormat('en', { dateStyle: 'medium' })

interface Props {
  report: ReportProperties
  onClose: () => void
}

export default function ReportDetails({ report, onClose }: Props) {
  const [photoFailed, setPhotoFailed] = useState(false)

  // escape closes the sheet
  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  const title = report.damage_type
    ? (DAMAGE_LABELS[report.damage_type] ?? report.damage_type)
    : 'Road damage'

  return (
    <div className="overlay" onClick={onClose}>
      <div
        className="sheet details"
        role="dialog"
        aria-modal="true"
        aria-labelledby="details-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="details-head">
          <h2 id="details-title">{title}</h2>
          <button className="details-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {photoFailed ? (
          <p className="details-photo details-photo-missing">Photo not available</p>
        ) : (
          <img
            key={report.id}
            className="details-photo"
            src={reportPhotoUrl(report.id)}
            alt={title}
            onError={() => setPhotoFailed(true)}
          />
        )}

        <div className="details-meta">
          {report.severity && (
            <span className={`severity-pill severity-${report.severity}`}>
              {SEVERITY_LABELS[report.severity]}
            </span>
          )}
          <span className="hint">Reported {dateFormat.format(new Date(report.created_at))}</span>
        </div>
      </div>
    </div>
  )
}
