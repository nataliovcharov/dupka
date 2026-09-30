import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router'

import type { AdminReport } from '../types'
import { fetchQueue, submitReview, UnauthorizedError, type ReviewInput } from './api'
import Logo from './Logo'
import ReviewCard from './ReviewCard'
import './admin.css'

// sessionStorage, so the token is gone when the tab closes
const TOKEN_KEY = 'dupka.adminToken'

function loadToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

function saveToken(token: string | null) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage blocked, the token just won't survive a reload
  }
}

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(loadToken)
  const [queue, setQueue] = useState<AdminReport[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const signOut = useCallback((message: string | null = null) => {
    saveToken(null)
    setToken(null)
    setQueue(null)
    setError(message)
  }, [])

  // a 401 means the token is wrong, so ask for it again
  const handleError = useCallback(
    (err: unknown) => {
      if (err instanceof UnauthorizedError) signOut(err.message)
      else setError(err instanceof Error ? err.message : 'Something went wrong')
    },
    [signOut],
  )

  useEffect(() => {
    if (!token) return
    let cancelled = false
    fetchQueue(token)
      .then((reports) => {
        if (!cancelled) setQueue(reports)
      })
      .catch((err) => {
        if (!cancelled) handleError(err)
      })
    return () => {
      cancelled = true
    }
  }, [token, refreshKey, handleError])

  function signIn(value: string) {
    saveToken(value)
    setError(null)
    setToken(value)
  }

  function refresh() {
    setQueue(null)
    setError(null)
    setRefreshKey((key) => key + 1)
  }

  const decide = useCallback(
    async (report: AdminReport, review: ReviewInput) => {
      if (!token) return
      try {
        await submitReview(token, report.id, review)
        setError(null)
        setQueue((current) => current && current.filter((r) => r.id !== report.id))
      } catch (err) {
        handleError(err)
      }
    },
    [token, handleError],
  )

  // skipped reports go to the back of the queue
  function skip(report: AdminReport) {
    setQueue((current) => current && [...current.filter((r) => r.id !== report.id), report])
  }

  if (!token) return <SignIn error={error} onSubmit={signIn} />

  const current = queue?.[0]

  return (
    <div className="admin">
      <header className="admin-bar">
        <Link to="/" className="admin-brand" aria-label="Back to the map">
          <Logo className="admin-logo" />
        </Link>
        <span className="admin-bar-divider" aria-hidden="true" />
        <span className="admin-bar-title">Review</span>
        {queue && <span className="admin-count">{queue.length} left</span>}
        <div className="admin-bar-end">
          <button className="admin-btn admin-btn-quiet" onClick={refresh}>
            Refresh
          </button>
          <button className="admin-btn admin-btn-quiet" onClick={() => signOut()}>
            Sign out
          </button>
        </div>
      </header>

      <main className="admin-main">
        {error && (
          <p className="admin-alert" role="alert">
            {error}
          </p>
        )}
        {queue === null && !error && <p className="admin-muted">Loading reports…</p>}
        {queue?.length === 0 && (
          <div className="admin-empty">
            <h2>All caught up</h2>
            <p className="admin-muted">No reports are waiting for review.</p>
            <button className="admin-btn admin-btn-secondary" onClick={refresh}>
              Check again
            </button>
          </div>
        )}
        {current && token && (
          <ReviewCard
            key={current.id}
            token={token}
            report={current}
            onDecide={(review) => decide(current, review)}
            onSkip={() => skip(current)}
            onError={handleError}
          />
        )}
      </main>
    </div>
  )
}

interface SignInProps {
  error: string | null
  onSubmit: (token: string) => void
}

function SignIn({ error, onSubmit }: SignInProps) {
  const [value, setValue] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const token = value.trim()
    if (token) onSubmit(token)
  }

  return (
    <div className="admin admin-center">
      <form className="admin-card signin" onSubmit={handleSubmit}>
        <Logo className="signin-logo" />
        <h1>Review queue</h1>
        <p className="admin-muted">Enter the admin token to continue.</p>
        <label className="field-label" htmlFor="admin-token">
          Admin token
        </label>
        <input
          id="admin-token"
          className="admin-input"
          type="password"
          autoComplete="current-password"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          autoFocus
        />
        {error && (
          <p className="admin-alert" role="alert">
            {error}
          </p>
        )}
        <button className="admin-btn admin-btn-primary" type="submit" disabled={!value.trim()}>
          Sign in
        </button>
      </form>
    </div>
  )
}
