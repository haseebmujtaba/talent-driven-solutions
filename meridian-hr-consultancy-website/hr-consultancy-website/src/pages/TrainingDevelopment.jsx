import { useEffect } from 'react'
import ServicePageLayout from './ServicePageLayout'
import { getPillarBySlug } from '../data/servicesData'

const pillar = getPillarBySlug('training-development')

export default function TrainingDevelopment() {
  useEffect(() => {
    document.title = 'Training & Development | Meridian Consulting'
  }, [])

  return <ServicePageLayout pillar={pillar} />
}
