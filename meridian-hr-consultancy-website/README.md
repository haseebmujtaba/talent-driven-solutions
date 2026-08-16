# Meridian — HR & Sustainability Consulting Website

A minimalist, corporate React website for an HR consultancy, built with Vite + React
and routed with React Router. Three dedicated pages cover the three service pillars:

- **HRM Solutions** — `/hrm-solutions`
- **Sustainability Solutions** — `/sustainability-solutions`
- **Training & Development Programs** — `/training-development`

Plus a homepage (`/`) and a contact page (`/contact`).

## Running it in VS Code

1. Open this folder in VS Code.
2. Open a terminal (`` Ctrl+` `` / `` Cmd+` ``) and install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
4. Open the URL Vite prints (usually `http://localhost:5173`).

To build a production version:
```bash
npm run build
```
This outputs static files to `dist/`, which you can deploy to any static host
(Vercel, Netlify, GitHub Pages, S3, etc.).

## Project structure

```
src/
  components/       Reusable UI: Navbar, Footer, service cards, sidebar nav, ring icon
  pages/            One file per route (Home, the 3 service pages, Contact, 404)
  data/
    servicesData.js  All service copy lives here — categories, descriptions, tags
  index.css         Design tokens (colors, fonts, spacing) and base styles
```

## Making it yours

- **Brand name / logo**: currently placeholder text "MERIDIAN" with a 3-ring SVG mark
  in `Navbar.jsx` and `Footer.jsx`. Swap in a real logo image if your client has one.
- **Contact details**: placeholder email/phone/address live in `Footer.jsx` and
  `Contact.jsx` — replace with the real details.
- **Contact form**: `src/pages/Contact.jsx` currently just shows a success message on
  submit. Wire `handleSubmit` up to a real backend, form service (Formspree, Resend,
  etc.), or email API before going live.
- **Service copy**: everything under each pillar (titles, descriptions, tag lists) is
  in `src/data/servicesData.js`. Edit this one file to update content on all three
  service pages — no need to touch the page components.
- **Colors/fonts**: all design tokens are CSS variables at the top of `src/index.css`
  (`--navy-950`, `--gold`, `--font-display`, etc.). Changing them there updates the
  whole site consistently.

## Notes

- No UI framework (Tailwind/MUI) is used — plain CSS files per component, scoped by
  class name, so there's nothing extra to learn or configure.
- Fonts (Fraunces, Inter, IBM Plex Mono) load from Google Fonts via `index.html`. For
  an offline build, self-host them instead.
