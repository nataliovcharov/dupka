import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { createReport } from '../api'
import { getCurrentPosition, isInNorthMacedonia, type LngLat } from '../geo'
import type { Report } from '../types'
import { resizeImage } from '../utils/image'
import LocationPicker from './LocationPicker'

interface Props {
  photo: File
  previewUrl: string
  fallbackLocation: LngLat // used until GPS answers, or if it never does
  onClose: () => void
  onSubmitted: (report: Report) => void
}

type Step = 'confirm' | 'sending' | 'done'

export default function ReportFlow({
  photo,
  previewUrl,
  fallbackLocation,
  onClose,
  onSubmitted,
}: Props) {
  const [step, setStep] = useState<Step>('confirm')
  const [location, setLocation] = useState<LngLat>(fallbackLocation)
  const [locationNote, setLocationNote] = useState('Finding your location…')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getCurrentPosition()
      .then((position) => {
        if (cancelled) return
        setLocation(position)
        setLocationNote('Drag the pin if it is not exactly on the damage.')
      })
      .catch(() => {
        if (cancelled) return
        setLocationNote('We could not get your location. Move the pin to the damage.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function submit() {
    if (!isInNorthMacedonia(location)) {
      setError('The location must be in North Macedonia.')
      return
    }
    setError(null)
    setStep('sending')
    try {
      const resized = await resizeImage(photo)
      const report = await createReport(resized, location)
      setStep('done')
      onSubmitted(report)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setStep('confirm')
    }
  }

  return (
    <div className="overlay">
      <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="report-title">
        {step === 'done' ? (
          <>
            <h2 id="report-title">Thank you!</h2>
            <p>
              Your report was sent. We check every photo before it goes on the public map,
              usually within a minute. Until then, you'll see it as a red ring.
            </p>
            <button className="button button-primary" onClick={onClose}>
              Done
            </button>
          </>
        ) : (
          <>
            <h2 id="report-title">Report road damage</h2>
            <img className="photo-preview" src={previewUrl} alt="Your photo of the damage" />
            <LocationPicker value={location} onChange={setLocation} />
            <p className="hint">{locationNote}</p>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <div className="actions">
              <button className="button" onClick={onClose} disabled={step === 'sending'}>
                Cancel
              </button>
              <button
                className="button button-primary"
                onClick={submit}
                disabled={step === 'sending'}
              >
                {step === 'sending' ? 'Sending…' : 'Send report'}
              </button>
            </div>
            <p className="fine-print">
              Faces and number plates are blurred automatically.{' '}
              <Link to="/privacy">How we use your photo</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
