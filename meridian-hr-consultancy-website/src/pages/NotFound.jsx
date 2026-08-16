import { Link } from 'react-router-dom'
import './NotFound.css'

export default function NotFound() {
  return (
    <section className="not-found">
      <div className="container not-found__inner">
        <span className="eyebrow">404</span>
        <h1>That page doesn't exist.</h1>
        <p>The page you're looking for may have moved. Head back to the homepage to find your way.</p>
        <Link to="/" className="btn btn--dark">
          Back to home
        </Link>
      </div>
    </section>
  )
}
