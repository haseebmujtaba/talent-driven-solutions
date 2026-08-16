import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Resets scroll position to the top whenever the route pathname changes,
// so navigating between service pages doesn't retain the previous scroll offset.
export default function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}
