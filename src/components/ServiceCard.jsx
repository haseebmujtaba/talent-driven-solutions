import { Link } from 'react-router-dom'
import PillarRings from './PillarRings'
import './ServiceCard.css'

export default function ServiceCard({ pillar }) {
  return (
    <Link to={`/${pillar.slug}`} className="service-card">
      <div className="service-card__icon">
        <PillarRings active={pillar.ring} size={56} />
      </div>
      <span className="eyebrow">{pillar.eyebrow}</span>
      <h3 className="service-card__title">{pillar.name}</h3>
      <p className="service-card__desc">{pillar.cardDescription}</p>
      <ul className="service-card__tags">
        {pillar.previewTags.map((tag) => (
          <li key={tag}>{tag}</li>
        ))}
      </ul>
      <span className="service-card__link">View services →</span>
    </Link>
  )
}
