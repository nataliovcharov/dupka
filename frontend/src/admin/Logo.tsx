import logo from '../assets/logo.svg'
import logoLight from '../assets/logo-light.svg'

// white lettering when the system is in dark mode
export default function Logo({ className }: { className?: string }) {
  return (
    <picture>
      <source srcSet={logoLight} media="(prefers-color-scheme: dark)" />
      <img src={logo} alt="Dupka" className={className} />
    </picture>
  )
}
