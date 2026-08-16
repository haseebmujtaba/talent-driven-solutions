import { slugify } from './ServiceSidebar'
import './CategorySection.css'

// Categories are a set, not a sequence — so no numbered markers here.
// The gold rule against the heading is the only accent, echoing the
// sidebar's active-link indicator.
export default function CategorySection({ category }) {
  const id = slugify(category.title)

  return (
    <section id={id} className="cat-section">
      <h3>{category.title}</h3>
      <p className="cat-section__desc">{category.description}</p>
      <ul className="cat-section__tags">
        {category.tags.map((tag) => (
          <li key={tag}>{tag}</li>
        ))}
      </ul>
    </section>
  )
}
