import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

import { createReport } from '../api'
import { errorKey } from '../i18n/errors'
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
  const { t } = useTranslation()
  const [step, setStep] = useState<Step>('confirm')
  const [location, setLocation] = useState<LngLat>(fallbackLocation)
  // translation keys, so the texts follow the chosen language
  const [locationNote, setLocationNote] = useState('report.locating')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getCurrentPosition()
      .then((position) => {
        if (cancelled) return
        setLocation(position)
        setLocationNote('report.dragPin')
      })
      .catch(() => {
        if (cancelled) return
        setLocationNote('report.noLocation')
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function submit() {
    if (!isInNorthMacedonia(location)) {
      setError('report.outsideMacedonia')
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
      setError(errorKey(err))
      setStep('confirm')
    }
  }

  return (
    <div className="overlay">
      <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="report-title">
        {step === 'done' ? (
          <>
            <h2 id="report-title">{t('report.thanksTitle')}</h2>
            <p>{t('report.thanksBody')}</p>
            <button className="button button-primary" onClick={onClose}>
              {t('report.done')}
            </button>
          </>
        ) : (
          <>
            <h2 id="report-title">{t('report.title')}</h2>
            <img className="photo-preview" src={previewUrl} alt={t('report.photoAlt')} />
            <LocationPicker value={location} onChange={setLocation} />
            <p className="hint">{t(locationNote)}</p>
            {error && (
              <p className="form-error" role="alert">
                {t(error)}
              </p>
            )}
            <div className="actions">
              <button className="button" onClick={onClose} disabled={step === 'sending'}>
                {t('report.cancel')}
              </button>
              <button
                className="button button-primary"
                onClick={submit}
                disabled={step === 'sending'}
              >
                {step === 'sending' ? t('report.sending') : t('report.send')}
              </button>
            </div>
            <p className="fine-print">
              {t('report.blurNote')} <Link to="/privacy">{t('report.privacyLink')}</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
