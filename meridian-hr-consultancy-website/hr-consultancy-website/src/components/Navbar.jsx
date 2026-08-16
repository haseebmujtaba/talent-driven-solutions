import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import './Navbar.css'

const navItems = [
  { to: '/hrm-solutions', label: 'HRM Solutions' },
  { to: '/sustainability-solutions', label: 'Sustainability' },
  { to: '/training-development', label: 'Training' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <header className="nav">
      <div className="container nav__inner">
        <NavLink to="/" className="nav__brand" onClick={() => setOpen(false)}>
          <svg width="30" height="30" viewBox="0 0 64 64" aria-hidden="true">
            <circle cx="24" cy="26" r="12" fill="none" stroke="var(--gold)" strokeWidth="4" />
            <circle cx="40" cy="26" r="12" fill="none" stroke="var(--white)" strokeWidth="4" />
            <circle cx="32" cy="40" r="12" fill="none" stroke="var(--slate-light)" strokeWidth="4" />
          </svg>
          <span>MERIDIAN</span>
        </NavLink>

        <nav className={`nav__links ${open ? 'nav__links--open' : ''}`}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav__link ${isActive ? 'nav__link--active' : ''}`}
              onClick={() => setOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
          <NavLink to="/contact" className="btn btn--primary nav__cta" onClick={() => setOpen(false)}>
            Get in touch
          </NavLink>
        </nav>

        <button
          className="nav__toggle"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  )
}
