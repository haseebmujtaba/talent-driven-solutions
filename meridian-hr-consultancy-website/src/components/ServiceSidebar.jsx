import { useEffect, useState } from 'react'
import './ServiceSidebar.css'

const slugify = (str) =>
  str
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')

export default function ServiceSidebar({ categories }) {
  const [activeId, setActiveId] = useState(slugify(categories[0].title))

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
          }
        })
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
    )

    categories.forEach((cat) => {
      const el = document.getElementById(slugify(cat.title))
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [categories])

  return (
    <nav className="service-sidebar" aria-label="Service categories">
      <span className="eyebrow eyebrow--muted service-sidebar__label">On this page</span>
      <ul>
        {categories.map((cat) => {
          const id = slugify(cat.title)
          return (
            <li key={id}>
              <a href={`#${id}`} className={activeId === id ? 'is-active' : ''}>
                {cat.title}
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export { slugify }
