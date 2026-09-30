import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { LANGUAGES } from '../i18n'

function GlobeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const current = LANGUAGES.find((l) => l.code === i18n.resolvedLanguage) ?? LANGUAGES[0]

  // close on a click outside or on escape
  useEffect(() => {
    if (!open) return
    function handleClick(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  function choose(code: string) {
    i18n.changeLanguage(code)
    setOpen(false)
  }

  return (
    <div className="language" ref={rootRef}>
      <button
        className="language-button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`${t('header.language')}: ${current.name}`}
        onClick={() => setOpen((o) => !o)}
      >
        <GlobeIcon />
        <span>{current.short}</span>
      </button>
      {open && (
        <ul className="language-menu" role="menu">
          {LANGUAGES.map((language) => (
            <li key={language.code} role="none">
              <button
                role="menuitemradio"
                aria-checked={language.code === current.code}
                lang={language.code}
                onClick={() => choose(language.code)}
              >
                {language.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
