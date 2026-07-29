import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assetgen.core import *
from assetgen.pages_def import PAGES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES_DIR = os.path.join(ROOT, 'pages')

FRAME_COUNT = 64
ASPECT = 16 / 9
DESK_W = 1400
DESK_H = round(DESK_W / ASPECT)
MOB_W = 800
MOB_H = round(MOB_W / ASPECT)


def ease(t):
    return t * t * (3 - 2 * t)


def by_slug(slug):
    return next(p for p in PAGES if p['slug'] == slug)


def frame_ramen(w, h, t):
    e = ease(t)
    pal = by_slug('neon-ramen-rush')['pal']
    im = radial_gradient(w, h, [(0.0, '#3a1268'), (0.45, '#8b1e8f'), (1.0, '#120620')], center=(0.5, 0.42 - 0.03 * e))
    im = add_rays(im, (0.5, 0.4), n=20, color=hex2rgb('#ff2f8f'), alpha=int(lerp(18, 70, e)))
    im = draw_energy_rings(im, (0.5, 0.78), hex2rgb('#3ff6ff'), n=3, base_r=lerp(0.05, 0.22, e),
                            gap=0.07, alpha=int(lerp(40, 150, e)))
    d = ImageDraw.Draw(im, 'RGBA')
    bowl_y = h * 0.8
    bw = w * lerp(0.14, 0.2, e)
    d.ellipse([w * 0.5 - bw, bowl_y - bw * 0.4, w * 0.5 + bw, bowl_y + bw * 0.4], fill=hex2rgb('#ff2f8f') + (255,))
    d.ellipse([w * 0.5 - bw * 0.82, bowl_y - bw * 0.34, w * 0.5 + bw * 0.82, bowl_y + bw * 0.1], fill=hex2rgb('#3ff6ff') + (255,))
    # steam rising, fading as character powers up (steam -> sparks)
    for i in range(5):
        sx = w * 0.5 + (i - 2) * w * 0.03
        sy0 = bowl_y - bw * 0.3
        h_s = h * lerp(0.16, 0.03, e)
        d.line([(sx, sy0), (sx + math.sin(i + t * 6) * 10, sy0 - h_s)], fill=(255, 255, 255, int(lerp(140, 20, e))), width=4)
    origin_y = lerp(0.86, 0.74, e)
    scale = lerp(0.75, 1.08, e)
    pose = 'stand_power' if e > 0.5 else 'leap'
    im = draw_hero_figure(im, pal, origin=(0.5, origin_y), scale=scale, pose=pose, facing=1)
    if e > 0.15:
        im = add_sparkles(im, rnd_seed=int(t * 1000) + 1, n=int(lerp(2, 26, e)))
    im = halftone_overlay(im, cell=12, max_alpha=int(lerp(20, 55, e)))
    im = vignette(im, 0.5)
    return im


def frame_idol(w, h, t):
    e = ease(t)
    pal = by_slug('starlight-idol')['pal']
    im = radial_gradient(w, h, [(0.0, '#2a1060'), (0.5, '#5b1aa0'), (1.0, '#0c0620')], center=(0.5, 0.4))
    n_rays = int(lerp(6, 26, e))
    im = add_rays(im, (0.5, 0.32), n=max(4, n_rays), color=hex2rgb('#ffd23f'), alpha=int(lerp(15, 85, e)), spin=t * 0.4)
    scale = lerp(0.7, 1.1, e)
    origin_y = lerp(0.88, 0.76, e)
    pose = 'leap' if e < 0.5 else 'stand_power'
    im = draw_hero_figure(im, pal, origin=(0.5, origin_y), scale=scale, pose=pose, facing=1)
    if e > 0.1:
        im = add_sparkles(im, rnd_seed=int(t * 1000) + 2, n=int(lerp(4, 34, e)), colors=((255, 210, 80), (255, 255, 255)))
    if e > 0.55:
        im = impact_burst(im, (0.5, 0.3), color=hex2rgb('#ffd23f'), n=14, r_out=lerp(0.0, 0.5, (e - 0.55) / 0.45), alpha=140)
    im = halftone_overlay(im, cell=12, max_alpha=int(lerp(15, 45, e)))
    im = vignette(im, 0.45)
    return im


def frame_mecha(w, h, t):
    e = ease(t)
    pal = by_slug('mecha-overdrive')['pal']
    im = radial_gradient(w, h, [(0.0, '#123049'), (0.5, '#0c1c2e'), (1.0, '#050a12')], center=(0.5, 0.42))
    im = draw_energy_rings(im, (0.5, 0.7), hex2rgb('#3fd0ff'), n=4, base_r=lerp(0.03, 0.26, e), gap=0.07,
                            alpha=int(lerp(20, 150, e)))
    im = draw_hero_figure(im, pal, origin=(0.5, 0.76), scale=1.1, pose='stand_power', facing=1)
    # progressive armor plates snapping onto the silhouette
    plates = [
        (0.5, 0.5, 0.10), (0.38, 0.58, 0.07), (0.62, 0.58, 0.07),
        (0.5, 0.72, 0.09), (0.34, 0.78, 0.06), (0.66, 0.78, 0.06),
        (0.44, 0.32, 0.05), (0.56, 0.32, 0.05),
    ]
    d = ImageDraw.Draw(im, 'RGBA')
    n_on = e * len(plates)
    for i, (px, py, ps) in enumerate(plates):
        local = np_clip(n_on - i, 0, 1)
        if local <= 0:
            continue
        cx, cy = px * w, py * h
        s = ps * min(w, h) * (0.6 + 0.4 * local)
        a = int(220 * local)
        d.polygon([(cx - s, cy - s * 0.6), (cx + s, cy - s * 0.6), (cx + s * 0.7, cy + s * 0.6), (cx - s * 0.7, cy + s * 0.6)],
                  fill=hex2rgb('#3fd0ff') + (a,), outline=(255, 255, 255, a))
    if e > 0.2:
        im = add_sparkles(im, rnd_seed=int(t * 1000) + 3, n=int(lerp(2, 18, e)), colors=((150, 220, 255), (255, 255, 255)))
    im = halftone_overlay(im, cell=12, max_alpha=int(lerp(15, 40, e)))
    im = vignette(im, 0.5)
    return im


def np_clip(x, lo, hi):
    return max(lo, min(hi, x))


SEQUENCES = {
    'neon-ramen-rush': frame_ramen,
    'starlight-idol': frame_idol,
    'mecha-overdrive': frame_mecha,
}


def build(slug, fn):
    base = os.path.join(PAGES_DIR, slug, 'assets')
    d_desk = os.path.join(base, 'frames', 'desktop')
    d_mob = os.path.join(base, 'frames', 'mobile')
    os.makedirs(d_desk, exist_ok=True)
    os.makedirs(d_mob, exist_ok=True)
    urls, urls_mobile = [], []
    total = 0
    for i in range(FRAME_COUNT):
        t = i / (FRAME_COUNT - 1)
        im_d = fn(DESK_W, DESK_H, t)
        im_m = im_d.resize((MOB_W, MOB_H), Image.LANCZOS)
        name = f'{i+1:04d}.webp'
        pd = os.path.join(d_desk, name)
        pm = os.path.join(d_mob, name)
        save_webp(im_d, pd, quality=58, method=6)
        save_webp(im_m, pm, quality=52, method=6)
        # tighten if over budget
        q = 58
        while os.path.getsize(pd) > 40 * 1024 and q > 28:
            q -= 8
            save_webp(im_d, pd, quality=q, method=6)
        qm = 52
        while os.path.getsize(pm) > 40 * 1024 and qm > 24:
            qm -= 8
            save_webp(im_m, pm, quality=qm, method=6)
        total += os.path.getsize(pd) + os.path.getsize(pm)
        urls.append(f'assets/frames/desktop/{name}')
        urls_mobile.append(f'assets/frames/mobile/{name}')
        if i == FRAME_COUNT - 1:
            poster_path = os.path.join(base, 'frames', 'poster.webp')
            save_webp(im_d, poster_path, quality=80)
            total += os.path.getsize(poster_path)
    manifest = {
        'frameCount': FRAME_COUNT, 'width': DESK_W, 'height': DESK_H, 'format': 'webp',
        'urls': urls, 'urlsMobile': urls_mobile, 'poster': 'assets/frames/poster.webp',
    }
    with open(os.path.join(base, 'frames', 'manifest.json'), 'w') as f:
        json.dump(manifest, f)
    print(slug, 'frames:', FRAME_COUNT, 'total bytes:', total, f'({total/1024/1024:.2f} MB)')
    return total


if __name__ == '__main__':
    grand_total = 0
    for slug, fn in SEQUENCES.items():
        grand_total += build(slug, fn)
    print('GRAND TOTAL:', grand_total, f'({grand_total/1024/1024:.2f} MB)')
