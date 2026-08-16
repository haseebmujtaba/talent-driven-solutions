import { useEffect } from 'react'
import ServicePageLayout from './ServicePageLayout'
import { getPillarBySlug } from '../data/servicesData'

const pillar = getPillarBySlug('sustainability-solutions')

export default function SustainabilitySolutions() {
  useEffect(() => {
    document.title = 'Sustainability Solutions | Meridian Consulting'
  }, [])

  return <ServicePageLayout pillar={pillar} />
}
