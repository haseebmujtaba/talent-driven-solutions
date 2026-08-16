import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import ServiceCard from '../components/ServiceCard'
import { pillars } from '../data/servicesData'
import './Home.css'

export default function Home() {
  useEffect(() => {
    document.title = 'Meridian | HR & Sustainability Consulting'
  }, [])

  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="hero">
        <div className="container hero__inner">
          <div className="hero__text">
            <span className="eyebrow">HR &amp; Sustainability Advisory</span>
            <h1>
              One consultancy for people, planet, and the capability to run both.
            </h1>
            <p>
              We build the HR systems that run a business, the sustainability strategy that
              holds up to scrutiny, and the in-house training so your teams can carry both
              forward.
            </p>
            <div className="hero__actions">
              <Link to="/hrm-solutions" className="btn btn--primary">
                Explore services
              </Link>
              <Link to="/contact" className="btn btn--outline">
                Get in touch
              </Link>
            </div>
          </div>

          <div className="hero__diagram" aria-hidden="true">
            <svg viewBox="0 0 360 300" width="100%" height="100%">
              <circle cx="150" cy="120" r="72" fill="none" stroke="var(--gold)" strokeWidth="1.5" />
              <circle cx="250" cy="120" r="72" fill="none" stroke="var(--white)" strokeWidth="1.5" opacity="0.7" />
              <circle cx="200" cy="200" r="72" fill="none" stroke="var(--slate-light)" strokeWidth="1.5" opacity="0.6" />
              <text x="90" y="80" className="hero__diagram-label" fill="var(--gold)">HRM</text>
              <text x="270" y="80" className="hero__diagram-label" fill="var(--white)">SUSTAINABILITY</text>
              <text x="150" y="272" className="hero__diagram-label" fill="var(--slate-light)">TRAINING</text>
            </svg>
          </div>
        </div>
      </section>

      {/* ---------- Three pillars ---------- */}
      <section className="section pillars">
        <div className="container">
          <div className="pillars__head">
            <span className="eyebrow eyebrow--muted">What we do</span>
            <h2>Three ways we help</h2>
          </div>
          <div className="pillars__grid">
            {pillars.map((pillar) => (
              <ServiceCard key={pillar.slug} pillar={pillar} />
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Approach ---------- */}
      <section className="approach">
        <div className="container approach__inner">
          <div className="approach__text">
            <span className="eyebrow">Our approach</span>
            <h2>Built to be run, not just handed over.</h2>
            <p>
              A strategy document that sits in a drawer helps no one. Every engagement is
              scoped around what your team can realistically operate afterward — with the
              documentation, dashboards, and training to back it up.
            </p>
          </div>
          <ul className="approach__list">
            <li>
              <span className="approach__list-label">Grounded in your context</span>
              <p>No template playbooks — every recommendation is built around your structure, sector, and stage.</p>
            </li>
            <li>
              <span className="approach__list-label">Built for handover</span>
              <p>Policies, dashboards, and training designed so your own team can run them without us.</p>
            </li>
            <li>
              <span className="approach__list-label">One point of contact</span>
              <p>HR, sustainability, and training sit under one engagement — not three separate vendors.</p>
            </li>
          </ul>
        </div>
      </section>

      {/* ---------- CTA ---------- */}
      <section className="cta-band">
        <div className="container cta-band__inner">
          <div>
            <h2>Not sure which pillar you need?</h2>
            <p>Tell us where things stand today, and we'll point you to the right starting place.</p>
          </div>
          <Link to="/contact" className="btn btn--primary">
            Start a conversation
          </Link>
        </div>
      </section>
    </>
  )
}
