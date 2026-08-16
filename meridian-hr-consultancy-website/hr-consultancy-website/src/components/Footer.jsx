import { NavLink } from 'react-router-dom'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__col footer__brand">
          <div className="footer__logo">
            <svg width="26" height="26" viewBox="0 0 64 64" aria-hidden="true">
              <circle cx="24" cy="26" r="12" fill="none" stroke="var(--gold)" strokeWidth="4" />
              <circle cx="40" cy="26" r="12" fill="none" stroke="var(--white)" strokeWidth="4" />
              <circle cx="32" cy="40" r="12" fill="none" stroke="var(--slate-light)" strokeWidth="4" />
            </svg>
            <span>MERIDIAN</span>
          </div>
          <p className="footer__tagline">
            HR management, sustainability advisory, and training — under one roof.
          </p>
        </div>

        <div className="footer__col">
          <span className="eyebrow eyebrow--muted">Services</span>
          <NavLink to="/hrm-solutions">HRM Solutions</NavLink>
          <NavLink to="/sustainability-solutions">Sustainability Solutions</NavLink>
          <NavLink to="/training-development">Training &amp; Development</NavLink>
        </div>

        <div className="footer__col">
          <span className="eyebrow eyebrow--muted">Company</span>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/contact">Contact</NavLink>
        </div>

        <div className="footer__col">
          <span className="eyebrow eyebrow--muted">Contact</span>
          <a href="mailto:hello@meridian-consulting.com">hello@meridian-consulting.com</a>
          <a href="tel:+10000000000">+1 (000) 000-0000</a>
        </div>
      </div>

      <div className="container footer__bottom">
        <span>© {new Date().getFullYear()} Meridian Consulting. All rights reserved.</span>
      </div>
    </footer>
  )
}
