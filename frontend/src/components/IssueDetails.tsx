import { useEffect, useRef, useState, type TouchEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { fetchIssue, reportPhotoUrl } from '../api'
import { formatDate } from '../i18n'
import type { IssueDetails as Issue } from '../types'

const KNOWN_TYPES = ['D40', 'D20', 'D10', 'D00']

interface Props {
  issueId: string
  onClose: () => void
}

export default function IssueDetails({ issueId, onClose }: Props) {
  const { t } = useTranslation()
  const [issue, setIssue] = useState<Issue | null>(null)
  const [failed, setFailed] = useState(false)
  const [index, setIndex] = useState(0) // which report's photo is shown
  const [failedPhotos, setFailedPhotos] = useState<string[]>([])
  const touchStartX = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchIssue(issueId)
      .then((loaded) => {
        if (!cancelled) setIssue(loaded)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
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
  const type = issue?.damage_type
  const title = t(type && KNOWN_TYPES.includes(type) ? `damage.${type}` : 'damage.unknown')

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
          <button className="details-close" onClick={onClose} aria-label={t('details.close')}>
            ×
          </button>
        </div>

        {failed && (
          <p className="form-error" role="alert">
            {t('details.loadFailed')}
          </p>
        )}
        {!issue && !failed && (
          <p className="details-photo details-photo-missing">{t('details.loading')}</p>
        )}

        {issue && report && (
          <>
            <div
              className="gallery"
              onTouchStart={(event) => (touchStartX.current = event.touches[0].clientX)}
              onTouchEnd={handleTouchEnd}
            >
              {failedPhotos.includes(report.id) ? (
                <p className="details-photo details-photo-missing">{t('details.photoMissing')}</p>
              ) : (
                <img
                  key={report.id}
                  className="details-photo"
                  src={reportPhotoUrl(report.id)}
                  alt={t('details.photoAlt', { title, number: index + 1, count })}
                  onError={() => setFailedPhotos((ids) => [...ids, report.id])}
                />
              )}
              {count > 1 && (
                <>
                  <button className="gallery-nav gallery-prev" onClick={previous} aria-label={t('details.previous')}>
                    ‹
                  </button>
                  <button className="gallery-nav gallery-next" onClick={next} aria-label={t('details.next')}>
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
                  {t(`severityLong.${issue.severity}`)}
                </span>
              )}
              <span className="hint">
                {issue.report_count === 1
                  ? t('details.reportedOnce', { date: formatDate(issue.created_at) })
                  : t('details.reportedTimes', {
                      count: issue.report_count,
                      date: formatDate(issue.created_at),
                    })}
              </span>
            </div>
            {count > 1 && (
              <p className="hint">{t('details.thisPhoto', { date: formatDate(report.created_at) })}</p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
