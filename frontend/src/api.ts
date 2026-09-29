import type { ReportCollection } from './types'

// "/api" in development (Vite proxy); set VITE_API_URL for production
const API_URL = import.meta.env.VITE_API_URL ?? '/api'

export async function fetchReports(bbox: string): Promise<ReportCollection> {
  const response = await fetch(`${API_URL}/reports?bbox=${bbox}`)
  if (!response.ok) {
    throw new Error(`Failed to load reports (${response.status})`)
  }
  return response.json()
}
