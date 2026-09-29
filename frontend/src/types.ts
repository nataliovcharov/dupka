export type Severity = 'low' | 'medium' | 'high'
export type ReportStatus = 'pending' | 'processing' | 'done' | 'failed'

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
