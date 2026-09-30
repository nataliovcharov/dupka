import { API_URL, errorMessage } from '../api'
import type { AdminReport, DamageType, Severity } from '../types'

// thrown on 401, so the page can ask for the token again
export class UnauthorizedError extends Error {}

async function adminFetch(
  token: string,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}/admin${path}`, { ...init, headers })
  if (response.status === 401) throw new UnauthorizedError('Wrong or expired admin token')
  if (!response.ok) throw new Error(await errorMessage(response))
  return response
}

export async function fetchQueue(token: string): Promise<AdminReport[]> {
  const response = await adminFetch(token, '/reports?visibility=needs_review&limit=100')
  return response.json()
}

// photos need the token too, so they can't be a plain <img src>
export async function fetchPhoto(token: string, id: string): Promise<Blob> {
  const response = await adminFetch(token, `/reports/${id}/photo`)
  return response.blob()
}

export type ReviewInput =
  | { decision: 'approve'; damage_type: DamageType; severity: Severity }
  | { decision: 'reject' }

export async function submitReview(
  token: string,
  id: string,
  review: ReviewInput,
): Promise<AdminReport> {
  const response = await adminFetch(token, `/reports/${id}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(review),
  })
  return response.json()
}
