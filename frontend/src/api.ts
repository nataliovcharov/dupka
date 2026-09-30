import type { LngLat } from './geo'
import type { IssueCollection, IssueDetails, Report } from './types'

// "/api" in development (Vite proxy); set VITE_API_URL for production
export const API_URL = import.meta.env.VITE_API_URL ?? '/api'

// use the API's error message when there is one, so users see why it failed
export async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // not JSON
  }
  return `Request failed (${response.status})`
}

export async function fetchIssues(bbox: string): Promise<IssueCollection> {
  const response = await fetch(`${API_URL}/issues?bbox=${bbox}`)
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json()
}

export async function fetchIssue(id: string): Promise<IssueDetails> {
  const response = await fetch(`${API_URL}/issues/${id}`)
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json()
}

export async function createReport(photo: Blob, [lon, lat]: LngLat): Promise<Report> {
  const form = new FormData()
  form.append('photo', photo, 'photo.jpg')
  form.append('latitude', String(lat))
  form.append('longitude', String(lon))

  const response = await fetch(`${API_URL}/reports`, { method: 'POST', body: form })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json()
}

// public reports only, the API returns 404 for anything else
export function reportPhotoUrl(id: string): string {
  return `${API_URL}/reports/${id}/photo`
}
