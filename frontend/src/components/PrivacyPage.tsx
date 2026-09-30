import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

import logo from '../assets/logo.svg'
import { formatDate } from '../i18n'
import LanguageSwitcher from './LanguageSwitcher'

const UPDATED = '2026-09-30'

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="policy-section">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  )
}

// keep in step with the backend: hidden_photo_days and upload_rate_limit
export default function PrivacyPage() {
  const { t } = useTranslation()

  return (
    <div className="page">
      <header className="page-header">
        <Link to="/" aria-label={t('privacy.backToMap')}>
          <img src={logo} alt="Dupka" className="app-logo" />
        </Link>
        <div className="header-end">
          <Link to="/" className="back-link">
            <span aria-hidden="true">←</span> {t('privacy.backToMap')}
          </Link>
          <LanguageSwitcher />
        </div>
      </header>

      <main className="page-body">
        <h1>{t('privacy.title')}</h1>
        <p className="hint">{t('privacy.updated', { date: formatDate(UPDATED) })}</p>

        <Section title={t('privacy.collectTitle')}>
          <p>{t('privacy.collect1')}</p>
          <p>{t('privacy.collect2')}</p>
        </Section>

        <Section title={t('privacy.blurTitle')}>
          <p>{t('privacy.blur')}</p>
        </Section>

        <Section title={t('privacy.publicTitle')}>
          <p>{t('privacy.public')}</p>
        </Section>

        <Section title={t('privacy.useTitle')}>
          <ul>
            <li>{t('privacy.use1')}</li>
            <li>{t('privacy.use2')}</li>
          </ul>
          <p>{t('privacy.use3')}</p>
        </Section>

        <Section title={t('privacy.technicalTitle')}>
          <p>{t('privacy.technical')}</p>
        </Section>

        <Section title={t('privacy.retentionTitle')}>
          <ul>
            <li>{t('privacy.retention1')}</li>
            <li>{t('privacy.retention2')}</li>
          </ul>
        </Section>

        <Section title={t('privacy.contactTitle')}>
          <p>{t('privacy.contact')}</p>
        </Section>
      </main>
    </div>
  )
}
