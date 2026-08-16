import { useEffect } from 'react'
import ServicePageLayout from './ServicePageLayout'
import { getPillarBySlug } from '../data/servicesData'

const pillar = getPillarBySlug('hrm-solutions')

export default function HRMSolutions() {
  useEffect(() => {
    document.title = 'HRM Solutions | Meridian Consulting'
  }, [])

  return <ServicePageLayout pillar={pillar} />
}
