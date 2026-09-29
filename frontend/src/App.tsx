import { useRef, useState, type ChangeEvent } from 'react'

import ReportFlow from './components/ReportFlow'
import ReportMap from './components/ReportMap'
import { SKOPJE, type LngLat } from './geo'
import './App.css'

interface Draft {
  photo: File
  previewUrl: string
}

export default function App() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [mapCenter, setMapCenter] = useState<LngLat>(SKOPJE)
  const [refreshKey, setRefreshKey] = useState(0)

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
        <h1>Dupka</h1>
      </header>

      <ReportMap refreshKey={refreshKey} onCenterChange={setMapCenter} />

      <button className="report-button" onClick={() => fileInputRef.current?.click()}>
        Report damage
      </button>
      {/* no capture attribute, so phones offer both "Take photo" and "Photo library" */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={handleFile}
      />

      {draft && (
        <ReportFlow
          photo={draft.photo}
          previewUrl={draft.previewUrl}
          fallbackLocation={mapCenter}
          onClose={closeFlow}
          onSubmitted={() => setRefreshKey((key) => key + 1)}
        />
      )}
    </main>
  )
}
