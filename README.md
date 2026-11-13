# VAAQRI website — static build (V4)

Generated from the Claude Design boards by `build.py` (in the design project). Six static pages, no build step, no dependencies beyond Google Fonts.

- `index.html` — landing page. The hero console prototype is plain JS (template + sample data live inside the page).
- `hub.html`, `topic.html`, `article.html`, `glossary.html` — Intelligence hub pages.
- `privacy.html` — draft privacy notice (review before launch; `#terms` placeholder).
- `favicon.svg`, `robots.txt`, `sitemap.xml`.

## Host it
Upload the folder as-is to any static host (Netlify, Vercel, Cloudflare Pages, GitHub Pages, S3). `index.html` is the entry.

## Before go-live
1. Rebuild with your domain so canonical URLs, Open Graph and the sitemap are absolute:
   `python3 build.py --site-url https://www.yourdomain.co.uk`
2. Wire the demo form. Pass `--form-endpoint https://...` (a Formspree / Basin / Netlify Function / your own API URL that accepts a JSON POST and returns 2xx on success).
   The page only shows "Request sent" when the endpoint answers 2xx; without an endpoint it shows an honest error. Fields: name, role, email, company, locations, interest, page. A honeypot field (`website`) and a 2.5 s timing check are applied client-side; keep server-side validation too.
3. Review `privacy.html` and add a contact address.
4. Add an `og:image` (1200×630) if you want rich link previews.

## Notes
- All motion respects `prefers-reduced-motion`. Section highlights use IntersectionObserver (every modern browser).
- Sample data in the prototype and the capability screens is labelled as sample data in the UI.
