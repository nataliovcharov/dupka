import type { ReactNode } from 'react'
import { Link } from 'react-router'

import logo from '../assets/logo.svg'

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
  return (
    <div className="page">
      <header className="page-header">
        <Link to="/" aria-label="Back to the map">
          <img src={logo} alt="Dupka" className="app-logo" />
        </Link>
        <Link to="/" className="back-link">
          <span aria-hidden="true">←</span> Back to map
        </Link>
      </header>

      <main className="page-body">
        <h1>Privacy</h1>
        <p className="hint">Last updated 30 September 2026</p>

        <Section title="What we collect">
          <p>
            When you report road damage we keep the photo, the location you confirm on the map and
            the time. We don't ask for your name, email or an account.
          </p>
          <p>
            Photos from phones often carry hidden data, like where and with which camera they were
            taken. We remove all of it as soon as the photo arrives.
          </p>
        </Section>

        <Section title="Faces and number plates">
          <p>
            Faces and number plates are found and blurred automatically before anyone else can see
            the photo. We only keep the blurred version. If blurring fails, the photo is never
            shown.
          </p>
        </Section>

        <Section title="What is public">
          <p>
            Once a report is checked, the blurred photo, its location, the type of damage, how bad
            it is and the date appear on the public map. Reports of the same spot are shown
            together.
          </p>
        </Section>

        <Section title="How we use it">
          <ul>
            <li>To show road damage on the map.</li>
            <li>
              To improve the automatic damage detection. Photos and our review decisions are used
              to train and test the model.
            </li>
          </ul>
          <p>
            Photos are checked on our own server. They are not sent to other companies for
            analysis, and we don't sell or share them.
          </p>
        </Section>

        <Section title="Technical data">
          <p>
            To stop automated abuse, we count uploads per IP address for up to a day. The count is
            kept in memory only and is not stored with your report. Our hosting provider may keep
            standard server logs.
          </p>
        </Section>

        <Section title="How long we keep it">
          <ul>
            <li>Public reports stay while the damage is on the map.</li>
            <li>Photos of reports we don't publish are deleted after 30 days.</li>
          </ul>
        </Section>

        <Section title="Questions and removal">
          <p>
            Contact details for questions and removal requests will be added here before launch.
          </p>
        </Section>
      </main>
    </div>
  )
}
