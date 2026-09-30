import { useEffect, useEffectEvent, useState } from 'react'

import type { AdminReport, DamageType, Detection, Severity } from '../types'
import { fetchPhoto, UnauthorizedError, type ReviewInput } from './api'

// same as the settings in backend/app/core/config.py
const MIN_CONFIDENCE = 0.28
const ROAD_THRESHOLD = 0.5
const UNSAFE_THRESHOLD = 0.2

const DAMAGE_TYPES: { value: DamageType; label: string }[] = [
  { value: 'D40', label: 'Pothole' },
  { value: 'D20', label: 'Alligator' },
  { value: 'D10', label: 'Transverse' },
  { value: 'D00', label: 'Longitudinal' },
]

const SEVERITIES: { value: Severity; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

const relativeTime = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

function typeLabel(type: DamageType): string {
  return DAMAGE_TYPES.find((t) => t.value === type)?.label ?? type
}

// start from the model's answer, or its most confident detection
function initialType(report: AdminReport): DamageType {
  const known = DAMAGE_TYPES.find((t) => t.value === report.damage_type)
  if (known) return known.value
  const best = [...(report.detections ?? [])].sort((a, b) => b.confidence - a.confidence)[0]
  return best?.damage_type ?? 'D40'
}

function timeAgo(iso: string, now: number): string {
  const minutes = Math.round((new Date(iso).getTime() - now) / 60_000)
  if (Math.abs(minutes) < 60) return relativeTime.format(minutes, 'minute')
  const hours = Math.round(minutes / 60)
  if (Math.abs(hours) < 24) return relativeTime.format(hours, 'hour')
  return relativeTime.format(Math.round(hours / 24), 'day')
}

// why the report ended up here, in plain words
function reviewReason(report: AdminReport): string {
  if (report.status === 'failed') return 'Processing failed'
  if (report.safety && !report.safety.is_road) return 'Not recognised as a road'
  return 'No confident damage found'
}

interface Props {
  token: string
  report: AdminReport
  onDecide: (review: ReviewInput) => Promise<void>
  onSkip: () => void
  onError: (err: unknown) => void
}

export default function ReviewCard({ token, report, onDecide, onSkip, onError }: Props) {
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [photoFailed, setPhotoFailed] = useState(false)
  const [showBoxes, setShowBoxes] = useState(true)
  const [damageType, setDamageType] = useState<DamageType>(() => initialType(report))
  const [severity, setSeverity] = useState<Severity>(report.severity ?? 'medium')
  const [busy, setBusy] = useState(false)
  const [now] = useState(() => Date.now())

  useEffect(() => {
    let url: string | null = null
    let cancelled = false
    fetchPhoto(token, report.id)
      .then((blob) => {
        if (cancelled) return
        url = URL.createObjectURL(blob)
        setPhotoUrl(url)
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof UnauthorizedError) onError(err)
        else setPhotoFailed(true)
      })
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [token, report.id, onError])

  async function decide(review: ReviewInput) {
    if (busy) return
    setBusy(true)
    try {
      await onDecide(review)
    } finally {
      setBusy(false)
    }
  }

  const approve = () => decide({ decision: 'approve', damage_type: damageType, severity })
  const reject = () => decide({ decision: 'reject' })

  // keyboard shortcuts, ignored while typing or with modifier keys
  const onKey = useEffectEvent((event: KeyboardEvent) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return
    if (event.target instanceof HTMLInputElement) return
    const key = event.key.toLowerCase()
    if (key === 'a') approve()
    else if (key === 'r') reject()
    else if (key === 's') onSkip()
    else if (key === 'b') setShowBoxes((shown) => !shown)
  })

  useEffect(() => {
    const listener = (event: KeyboardEvent) => onKey(event)
    window.addEventListener('keydown', listener)
    return () => window.removeEventListener('keydown', listener)
  }, [])

  const detections = report.detections ?? []
  const scores = report.safety?.scores
  // nothing found or not a road: rejecting is the likely call
  const suggestReject = detections.length === 0 || report.safety?.is_road === false
  const mapUrl = `https://www.openstreetmap.org/?mlat=${report.latitude}&mlon=${report.longitude}#map=19/${report.latitude}/${report.longitude}`

  return (
    <article className="review">
      <section className="stage">
        {photoUrl ? (
          <div className="stage-frame">
            <img src={photoUrl} alt="Reported road" className="stage-photo" />
            {showBoxes && <Boxes detections={detections} />}
          </div>
        ) : (
          <p className="stage-placeholder">
            {photoFailed ? 'Photo not available' : 'Loading photo…'}
          </p>
        )}
        {detections.length > 0 && (
          <button
            className="stage-toggle"
            aria-pressed={showBoxes}
            onClick={() => setShowBoxes((shown) => !shown)}
          >
            {showBoxes ? 'Hide boxes' : 'Show boxes'} <kbd>B</kbd>
          </button>
        )}
      </section>

      <aside className="panel">
        <div className="panel-section">
          <div className="panel-meta">
            <span className="pill">{reviewReason(report)}</span>
            <time dateTime={report.created_at} className="admin-muted">
              {timeAgo(report.created_at, now)}
            </time>
          </div>
          <a className="panel-link" href={mapUrl} target="_blank" rel="noreferrer">
            {report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}
            <span aria-hidden="true"> ↗</span>
          </a>
        </div>

        {scores && (
          <div className="panel-section">
            <h3 className="panel-heading">Photo check</h3>
            <ScoreBar label="Road" value={scores.road} tone="road" threshold={ROAD_THRESHOLD} />
            <ScoreBar
              label="Unsafe"
              value={scores.unsafe}
              tone="unsafe"
              threshold={UNSAFE_THRESHOLD}
            />
            <ScoreBar label="Other" value={scores.other} tone="other" />
          </div>
        )}

        <div className="panel-section">
          <h3 className="panel-heading">Detections</h3>
          {detections.length === 0 ? (
            <p className="admin-muted">Nothing found</p>
          ) : (
            <ul className="detections">
              {[...detections]
                .sort((a, b) => b.confidence - a.confidence)
                .map((d, i) => (
                  <li key={i} className={d.confidence < MIN_CONFIDENCE ? 'is-weak' : undefined}>
                    <span className={`swatch swatch-${d.damage_type}`} />
                    <span>{typeLabel(d.damage_type)}</span>
                    <span className="detections-conf">{Math.round(d.confidence * 100)}%</span>
                  </li>
                ))}
            </ul>
          )}
        </div>

        <div className="panel-section">
          <h3 className="panel-heading">Decision</h3>
          <Segmented
            label="Damage type"
            options={DAMAGE_TYPES}
            value={damageType}
            onChange={setDamageType}
          />
          <Segmented
            label="Severity"
            options={SEVERITIES}
            value={severity}
            onChange={setSeverity}
          />
          <div className="decision">
            <button
              className={`admin-btn ${suggestReject ? 'admin-btn-danger-solid' : 'admin-btn-danger'}`}
              onClick={reject}
              disabled={busy}
            >
              Reject <kbd>R</kbd>
            </button>
            <button
              className={`admin-btn ${suggestReject ? 'admin-btn-secondary' : 'admin-btn-primary'}`}
              onClick={approve}
              disabled={busy}
            >
              Approve <kbd>A</kbd>
            </button>
          </div>
          <button className="admin-skip" onClick={onSkip} disabled={busy}>
            Skip for now <kbd>S</kbd>
          </button>
        </div>
      </aside>
    </article>
  )
}

// boxes are 0-1 of the photo size, so percentages line up at any size
function Boxes({ detections }: { detections: Detection[] }) {
  return (
    <div className="boxes" aria-hidden="true">
      {detections.map((d, i) => {
        const [x1, y1, x2, y2] = d.box
        const weak = d.confidence < MIN_CONFIDENCE
        return (
          <div
            key={i}
            className={`box box-${d.damage_type}${weak ? ' is-weak' : ''}`}
            style={{
              left: `${x1 * 100}%`,
              top: `${y1 * 100}%`,
              width: `${(x2 - x1) * 100}%`,
              height: `${(y2 - y1) * 100}%`,
            }}
          >
            <span className="box-label">
              {typeLabel(d.damage_type)} {Math.round(d.confidence * 100)}%
            </span>
          </div>
        )
      })}
    </div>
  )
}

interface ScoreBarProps {
  label: string
  value: number
  tone: string
  threshold?: number // tick where the decision flips
}

function ScoreBar({ label, value, tone, threshold }: ScoreBarProps) {
  return (
    <div className="score">
      <div className="score-head">
        <span>{label}</span>
        <span className="admin-muted">{Math.round(value * 100)}%</span>
      </div>
      <div className="score-bar">
        <div className="score-track">
          <div className={`score-fill score-${tone}`} style={{ width: `${value * 100}%` }} />
        </div>
        {threshold !== undefined && (
          <span
            className="score-tick"
            style={{ left: `${threshold * 100}%` }}
            title={`Threshold ${Math.round(threshold * 100)}%`}
          />
        )}
      </div>
    </div>
  )
}

interface SegmentedProps<T extends string> {
  label: string
  options: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
}

function Segmented<T extends string>({ label, options, value, onChange }: SegmentedProps<T>) {
  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <div className="segmented" role="radiogroup" aria-label={label}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={option.value === value}
            className="segment"
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
