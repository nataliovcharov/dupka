import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import { en } from './en'
import { mk } from './mk'

// each language in its own name, so people can find theirs
export const LANGUAGES = [
  { code: 'mk', name: 'Македонски', short: 'МК' },
  { code: 'en', name: 'English', short: 'EN' },
] as const

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, mk: { translation: mk } },
    supportedLngs: LANGUAGES.map((l) => l.code),
    nonExplicitSupportedLngs: true, // "en-GB" counts as "en"
    fallbackLng: 'mk', // the app is for Skopje
    // a saved choice first, then the browser's language
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'dupka.language',
      caches: ['localStorage'],
    },
    interpolation: { escapeValue: false }, // react escapes already
  })

// screen readers use it to pick the right voice
function setPageLanguage(language: string) {
  document.documentElement.lang = language
}
i18n.on('languageChanged', setPageLanguage)
setPageLanguage(i18n.resolvedLanguage ?? 'mk')

// dates in the chosen language, e.g. "30 септ. 2026"
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(i18n.resolvedLanguage, { dateStyle: 'medium' }).format(
    new Date(iso),
  )
}

export default i18n
