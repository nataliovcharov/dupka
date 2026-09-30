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

export type DamageType = 'D00' | 'D10' | 'D20' | 'D40'

export interface Detection {
  damage_type: DamageType
  confidence: number
  box: [number, number, number, number] // x1, y1, x2, y2 as 0-1 of the photo size
}

export interface Safety {
  scores: { road: number; unsafe: number; other: number }
  unsafe: boolean
  is_road: boolean
}

export interface Review {
  decision: 'approve' | 'reject'
  damage_type: DamageType | null
  severity: Severity | null
  model_damage_type: DamageType | null
  model_severity: Severity | null
  reviewer: string
  created_at: string
}

// a report with everything a reviewer needs, from GET /admin/reports
export interface AdminReport extends Report {
  detections: Detection[] | null
  safety: Safety | null
  privacy: { faces: number; plates: number } | null // how many were blurred
  last_review: Review | null
}

// one piece of damage on the map, reports of the same spot are grouped into it
export interface IssueProperties {
  id: string
  damage_type: DamageType | null
  severity: Severity | null
  report_count: number
  last_reported_at: string
}

export interface IssueFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] } // [lon, lat]
  properties: IssueProperties
}

export interface IssueCollection {
  type: 'FeatureCollection'
  features: IssueFeature[]
}

// from GET /issues/{id}, reports are newest first
export interface IssueDetails {
  id: string
  latitude: number
  longitude: number
  damage_type: DamageType | null
  severity: Severity | null
  report_count: number
  created_at: string
  last_reported_at: string
  reports: { id: string; damage_type: string | null; severity: Severity | null; created_at: string }[]
}
