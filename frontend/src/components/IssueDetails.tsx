import { useEffect, useRef, useState, type TouchEvent } from 'react'

import { fetchIssue, reportPhotoUrl } from '../api'
import type { IssueDetails as Issue, Severity } from '../types'

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

function formatDate(iso: string): string {
  return dateFormat.format(new Date(iso))
}

interface Props {
  issueId: string
  onClose: () => void
}

export default function IssueDetails({ issueId, onClose }: Props) {
  const [issue, setIssue] = useState<Issue | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [index, setIndex] = useState(0) // which report's photo is shown
  const [failedPhotos, setFailedPhotos] = useState<string[]>([])
  const touchStartX = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchIssue(issueId)
      .then((loaded) => {
        if (!cancelled) setIssue(loaded)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load this report')
      })
    return () => {
      cancelled = true
    }
  }, [issueId])

  const count = issue?.reports.length ?? 0
  const previous = () => setIndex((i) => (i - 1 + count) % count)
  const next = () => setIndex((i) => (i + 1) % count)

  // swipe left or right on phones
  function handleTouchEnd(event: TouchEvent) {
    const start = touchStartX.current
    touchStartX.current = null
    if (start === null || count < 2) return
    const distance = event.changedTouches[0].clientX - start
    if (distance > 40) previous()
    else if (distance < -40) next()
  }

  // escape closes, arrow keys move between photos
  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
      if (count < 2) return
      if (event.key === 'ArrowLeft') setIndex((i) => (i - 1 + count) % count)
      if (event.key === 'ArrowRight') setIndex((i) => (i + 1) % count)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose, count])

  const report = issue?.reports[index]
  const title = issue?.damage_type
    ? (DAMAGE_LABELS[issue.damage_type] ?? issue.damage_type)
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

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {!issue && !error && <p className="details-photo details-photo-missing">Loading…</p>}

        {issue && report && (
          <>
            <div
              className="gallery"
              onTouchStart={(event) => (touchStartX.current = event.touches[0].clientX)}
              onTouchEnd={handleTouchEnd}
            >
              {failedPhotos.includes(report.id) ? (
                <p className="details-photo details-photo-missing">Photo not available</p>
              ) : (
                <img
                  key={report.id}
                  className="details-photo"
                  src={reportPhotoUrl(report.id)}
                  alt={`${title}, photo ${index + 1} of ${count}`}
                  onError={() => setFailedPhotos((ids) => [...ids, report.id])}
                />
              )}
              {count > 1 && (
                <>
                  <button className="gallery-nav gallery-prev" onClick={previous} aria-label="Previous photo">
                    ‹
                  </button>
                  <button className="gallery-nav gallery-next" onClick={next} aria-label="Next photo">
                    ›
                  </button>
                  <span className="gallery-count">
                    {index + 1} / {count}
                  </span>
                </>
              )}
            </div>

            <div className="details-meta">
              {issue.severity && (
                <span className={`severity-pill severity-${issue.severity}`}>
                  {SEVERITY_LABELS[issue.severity]}
                </span>
              )}
              <span className="hint">
                {issue.report_count === 1
                  ? `Reported ${formatDate(issue.created_at)}`
                  : `Reported ${issue.report_count} times, first on ${formatDate(issue.created_at)}`}
              </span>
            </div>
            {count > 1 && <p className="hint">This photo: {formatDate(report.created_at)}</p>}
          </>
        )}
      </div>
    </div>
  )
}
