import { ApiError } from '../api'

// the API answers in english, so errors are shown by status instead
export function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 413) return 'errors.tooLarge'
    if (err.status === 415) return 'errors.wrongType'
    if (err.status === 422) return 'errors.notAPhoto'
    if (err.status === 429) return 'errors.tooMany'
    return 'errors.generic'
  }
  // fetch throws a TypeError when there's no connection
  if (err instanceof TypeError) return 'errors.network'
  return 'errors.generic'
}
