/**
 * Generative Scroll Sequence — scroll-scrub runtime.
 * Framework-agnostic; adapt to STACK. The object-fit:cover math in draw() is the
 * whole point of this file — do NOT "simplify" it away.
 *
 * manifest.json shape:
 *   { frameCount, width, height, format,
 *     urls: string[], urlsMobile?: string[], poster: string }
 */
export async function initGSS({
  manifestUrl = 'frames/manifest.json',
  track,        // tall scroll track element (300-400vh)
  canvas,       // sticky <canvas> that fills the viewport
  poster,       // <img> shown for reduced-motion / fallbacks (hidden until used)
  progressEl,   // optional element that displays preload progress
  mobileQuery = '(max-width: 800px)',
} = {}) {
  if (!track || !canvas) throw new Error('initGSS: track and canvas are required');

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const conn = navigator.connection || {};
  const slowNet = conn.saveData === true || /(?:^|-)(2g|3g)$/.test(conn.effectiveType || '');

  const manifest = await fetch(manifestUrl, { cache: 'force-cache' }).then((r) => r.json());
  const useMobile = matchMedia(mobileQuery).matches && Array.isArray(manifest.urlsMobile);
  const urls = useMobile ? manifest.urlsMobile : manifest.urls;
  const posterUrl = manifest.poster || urls[urls.length - 1];

  // showPoster is a function declaration, so it is hoisted and safe to call above.
  function showPoster() {
    if (poster) { poster.src = posterUrl; poster.hidden = false; }
    canvas.hidden = true;
    if (progressEl) progressEl.hidden = true;
  }

  // --- Fallbacks: render the final still, fetch ZERO sequence frames. ---
  if (reduceMotion || slowNet) return showPoster();

  // --- Stage 5: preload + decode gate. Scrub stays disabled until every frame decodes. ---
  let done = 0;
  const frames = new Array(urls.length);
  try {
    await Promise.all(
      urls.map(async (u, i) => {
        const img = new Image();
        img.decoding = 'async';
        img.src = u;
        await img.decode();
        frames[i] = img;
        done += 1;
        if (progressEl) progressEl.textContent = Math.round((done / urls.length) * 100) + '%';
      })
    );
  } catch {
    return showPoster(); // decode failure -> static poster, never a blank canvas
  }
  if (progressEl) progressEl.hidden = true;

  // --- Stage 6: scroll-scrub runtime. ---
  const ctx = canvas.getContext('2d', { alpha: false });
  let cw = 0, ch = 0, lastIndex = -1, dirty = true;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const box = canvas.getBoundingClientRect();
    cw = Math.max(1, Math.round(box.width * dpr));
    ch = Math.max(1, Math.round(box.height * dpr));
    canvas.width = cw;   // resizing clears the bitmap...
    canvas.height = ch;
    lastIndex = -1;      // ...so force a redraw of the current frame
    dirty = true;
  }

  // object-fit: cover, computed by hand. This is where portrait source meets
  // landscape viewport — the most common bug in this whole effect.
  function draw(img) {
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const scale = Math.max(cw / iw, ch / ih);
    const dw = iw * scale, dh = ih * scale;
    const dx = (cw - dw) / 2, dy = (ch - dh) / 2;
    ctx.drawImage(img, 0, 0, iw, ih, dx, dy, dw, dh);
  }

  // A passive scroll listener may ONLY flag work; it must never read scrollY itself.
  addEventListener('scroll', () => { dirty = true; }, { passive: true });
  addEventListener('resize', resize, { passive: true });

  function loop() {
    if (dirty) {
      dirty = false;
      const rect = track.getBoundingClientRect();
      const trackTop = window.scrollY + rect.top;
      const denom = track.offsetHeight - window.innerHeight;
      const progress = denom > 0
        ? Math.min(1, Math.max(0, (window.scrollY - trackTop) / denom))
        : 0;
      const index = Math.round(progress * (frames.length - 1));
      if (index !== lastIndex) {   // most scroll ticks land on the same frame
        lastIndex = index;
        draw(frames[index]);
      }
    }
    requestAnimationFrame(loop);
  }

  resize();
  canvas.hidden = false;
  requestAnimationFrame(loop);
}
