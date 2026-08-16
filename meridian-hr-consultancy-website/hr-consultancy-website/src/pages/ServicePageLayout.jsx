import { Link } from 'react-router-dom'
import PillarRings from '../components/PillarRings'
import ServiceSidebar from '../components/ServiceSidebar'
import CategorySection from '../components/CategorySection'
import { pillars } from '../data/servicesData'
import './ServicePageLayout.css'

export default function ServicePageLayout({ pillar }) {
  const otherPillars = pillars.filter((p) => p.slug !== pillar.slug)

  return (
    <>
      <section className="service-hero">
        <div className="container service-hero__inner">
          <div className="service-hero__text">
            <span className="eyebrow">{pillar.eyebrow}</span>
            <h1>{pillar.name}</h1>
            <p>{pillar.intro}</p>
          </div>
          <PillarRings active={pillar.ring} size={104} />
        </div>
      </section>

      <section className="section service-body">
        <div className="container service-body__grid">
          <ServiceSidebar categories={pillar.categories} />
          <div className="service-body__content">
            {pillar.categories.map((cat) => (
              <CategorySection key={cat.title} category={cat} />
            ))}
          </div>
        </div>
      </section>

      <section className="service-cross">
        <div className="container">
          <span className="eyebrow eyebrow--muted">Explore the other pillars</span>
          <div className="service-cross__grid">
            {otherPillars.map((p) => (
              <Link key={p.slug} to={`/${p.slug}`} className="service-cross__card">
                <PillarRings active={p.ring} size={40} />
                <div>
                  <h4>{p.name}</h4>
                  <p>{p.tagline}</p>
                </div>
                <span aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="service-cta">
        <div className="container service-cta__inner">
          <div>
            <h2>Let's talk about {pillar.shortName.toLowerCase()}.</h2>
            <p>Tell us what you're working with, and we'll tell you where we can help.</p>
          </div>
          <Link to="/contact" className="btn btn--primary">
            Get in touch
          </Link>
        </div>
      </section>
    </>
  )
}
