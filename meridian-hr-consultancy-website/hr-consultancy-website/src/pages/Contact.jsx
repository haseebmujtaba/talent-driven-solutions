import { useEffect, useState } from 'react'
import './Contact.css'

const topics = ['HRM Solutions', 'Sustainability Solutions', 'Training & Development', 'Something else']

export default function Contact() {
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    document.title = 'Contact | Meridian Consulting'
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    // No backend is wired up yet — replace this with a real submit handler
    // (an API route, email service, or form provider) before going live.
    setSubmitted(true)
  }

  return (
    <>
      <section className="contact-hero">
        <div className="container">
          <span className="eyebrow">Get in touch</span>
          <h1>Let's talk about what you need.</h1>
          <p>Tell us a bit about your organization, and we'll get back to you within two working days.</p>
        </div>
      </section>

      <section className="section contact-body">
        <div className="container contact-body__grid">
          <div className="contact-info">
            <div>
              <span className="eyebrow eyebrow--muted">Email</span>
              <a href="mailto:hello@meridian-consulting.com">hello@meridian-consulting.com</a>
            </div>
            <div>
              <span className="eyebrow eyebrow--muted">Phone</span>
              <a href="tel:+10000000000">+1 (000) 000-0000</a>
            </div>
            <div>
              <span className="eyebrow eyebrow--muted">Office</span>
              <p>Add your office address here.</p>
            </div>
          </div>

          {submitted ? (
            <div className="contact-success">
              <h3>Thanks — we've got it.</h3>
              <p>Your message has been noted. Someone from our team will follow up shortly.</p>
            </div>
          ) : (
            <form className="contact-form" onSubmit={handleSubmit}>
              <div className="contact-form__row">
                <label>
                  Name
                  <input type="text" name="name" required placeholder="Your full name" />
                </label>
                <label>
                  Company
                  <input type="text" name="company" placeholder="Organization name" />
                </label>
              </div>
              <div className="contact-form__row">
                <label>
                  Email
                  <input type="email" name="email" required placeholder="you@company.com" />
                </label>
                <label>
                  Which service?
                  <select name="topic" defaultValue={topics[0]}>
                    {topics.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label>
                Message
                <textarea name="message" rows={5} required placeholder="What are you trying to solve?" />
              </label>
              <button type="submit" className="btn btn--primary">
                Send message
              </button>
            </form>
          )}
        </div>
      </section>
    </>
  )
}
