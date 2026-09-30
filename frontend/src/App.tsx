import { useRef, useState, type ChangeEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

import IssueDetails from './components/IssueDetails'
import LanguageSwitcher from './components/LanguageSwitcher'
import ReportFlow from './components/ReportFlow'
import ReportMap from './components/ReportMap'
import { SKOPJE, type LngLat } from './geo'
import type { Report } from './types'
import logo from './assets/logo.svg'
import './App.css'

interface Draft {
  photo: File
  previewUrl: string
}

export default function App() {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [mapCenter, setMapCenter] = useState<LngLat>(SKOPJE)
  const [refreshKey, setRefreshKey] = useState(0)
  // kept only while the page is open, the map shows them before they are approved
  const [myReports, setMyReports] = useState<Report[]>([])
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null)

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const photo = event.target.files?.[0]
    event.target.value = '' // lets the same photo be picked again later
    if (photo) setDraft({ photo, previewUrl: URL.createObjectURL(photo) })
  }

  function closeFlow() {
    if (draft) URL.revokeObjectURL(draft.previewUrl)
    setDraft(null)
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>
          <img src={logo} alt="Dupka" className="app-logo" />
        </h1>
        <div className="header-end">
          <Link to="/privacy" className="header-link">
            {t('header.privacy')}
          </Link>
          <LanguageSwitcher />
        </div>
      </header>

      <ReportMap
        refreshKey={refreshKey}
        onCenterChange={setMapCenter}
        myReports={myReports}
        onSelect={setSelectedIssue}
      />

      <footer className="action-bar">
        <button className="report-button" onClick={() => fileInputRef.current?.click()}>
          {t('map.reportButton')}
        </button>
      </footer>
      {/* no capture attribute, so phones offer both "Take photo" and "Photo library" */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={handleFile}
      />

      {selectedIssue && (
        <IssueDetails issueId={selectedIssue} onClose={() => setSelectedIssue(null)} />
      )}

      {draft && (
        <ReportFlow
          photo={draft.photo}
          previewUrl={draft.previewUrl}
          fallbackLocation={mapCenter}
          onClose={closeFlow}
          onSubmitted={(report) => {
            setMyReports((reports) => [...reports, report])
            setRefreshKey((key) => key + 1)
          }}
        />
      )}
    </main>
  )
}
