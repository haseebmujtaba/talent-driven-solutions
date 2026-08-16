import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ScrollToTop from './components/ScrollToTop'
import Home from './pages/Home'
import HRMSolutions from './pages/HRMSolutions'
import SustainabilitySolutions from './pages/SustainabilitySolutions'
import TrainingDevelopment from './pages/TrainingDevelopment'
import Contact from './pages/Contact'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <div className="app">
      <ScrollToTop />
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/hrm-solutions" element={<HRMSolutions />} />
          <Route path="/sustainability-solutions" element={<SustainabilitySolutions />} />
          <Route path="/training-development" element={<TrainingDevelopment />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
