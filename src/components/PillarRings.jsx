// The three rings represent the three pillars: HRM (top-left), Sustainability
// (top-right), Training (bottom). Passing `active` dims the other two so the
// same motif can indicate "which pillar am I looking at" across the site.
const RING_ORDER = ['hrm', 'sustainability', 'training']

export default function PillarRings({ active, size = 120 }) {
  const colorFor = (ring) => {
    if (!active) return 'var(--gold)'
    return ring === active ? 'var(--gold)' : 'rgba(255,255,255,0.16)'
  }

  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="24" cy="26" r="14" fill="none" stroke={colorFor('hrm')} strokeWidth="3" />
      <circle cx="40" cy="26" r="14" fill="none" stroke={colorFor('sustainability')} strokeWidth="3" />
      <circle cx="32" cy="42" r="14" fill="none" stroke={colorFor('training')} strokeWidth="3" />
    </svg>
  )
}

export { RING_ORDER }
