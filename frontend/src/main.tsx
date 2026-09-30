import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router'
import './index.css'
import App from './App.tsx'
import PrivacyPage from './components/PrivacyPage.tsx'

const router = createBrowserRouter([
  { path: '/', element: <App /> },
  {
    path: '/admin',
    // loaded only on /admin, so map users never download it
    lazy: {
      Component: async () => (await import('./admin/AdminPage.tsx')).default,
    },
  },
  { path: '/privacy', element: <PrivacyPage /> },
  { path: '*', element: <Navigate to="/" replace /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
