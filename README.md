# Anime Scroll Landings

Eleven anime-flavored scrollytelling landing pages, one gallery. Static site, no build step, no framework — pure HTML/CSS/JS, deploy-as-is.

- `index.html` — colorful gallery linking every world, with thumbnails.
- `pages/<slug>/index.html` — one self-contained page per world (own `assets/` folder: images, css, js).
- Three pages (**Neon Ramen Rush**, **Starlight Idol**, **Mecha Overdrive**) use a real scroll-scrubbed frame-sequence hero (a `<canvas>` painted frame-by-frame as you scroll, per the `generative-scroll-sequence` pattern: preload+decode gate, hand-computed `object-fit: cover` math, `prefers-reduced-motion` short-circuit before any frame downloads). See `pages/<slug>/assets/frames/manifest.json` and `assets/js/scrubber.js`.
- The other eight pages use sticky-scene "storyboard cuts" (CSS `position: sticky` scenes driven by a `--scene-progress` custom property) plus reveal-on-scroll and parallax, via the shared `assets/js/reveal.js`.
- `assetgen/` — the Python/PIL procedural art generator used to make every character, background, and GSS keyframe on this site (see note below).
- `shared/` — canonical copies of the CSS/JS toolkit and the GSS skill reference runtime, copied into each page's `assets/` folder.

## About the artwork

No image-generation backend (Higgsfield MCP) was reachable in the session that built this site, so all artwork is generated algorithmically in a bold flat "anime key-visual poster" style — gradient skies, halftone shading, color-blocked character silhouettes, speed lines, sparkles, impact bursts — rather than photoreal/AI-illustrated anime art. See `assetgen/core.py` and `assetgen/generate_pages.py` / `assetgen/gss_gen.py`.
