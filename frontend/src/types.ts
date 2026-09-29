export type Severity = 'low' | 'medium' | 'high'
export type ReportStatus = 'pending' | 'processing' | 'done' | 'failed'
export type ReportVisibility = 'pending' | 'public' | 'needs_review' | 'hidden'

// one report, as returned by POST /reports and GET /reports/{id}
export interface Report {
  id: string
  status: ReportStatus
  visibility: ReportVisibility
  latitude: number
  longitude: number
  damage_type: string | null
  severity: Severity | null
  created_at: string
}

export interface ReportProperties {
  id: string
  status: ReportStatus
  damage_type: string | null
  severity: Severity | null
  created_at: string
}

export interface ReportFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] } // [lon, lat]
  properties: ReportProperties
}

export interface ReportCollection {
  type: 'FeatureCollection'
  features: ReportFeature[]
}
