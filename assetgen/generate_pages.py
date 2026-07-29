import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assetgen.core import *
from assetgen.pages_def import PAGES

OUT_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pages')


def make_bg(w, h, p, ang=115):
    if p['bg'] == 'radial':
        return radial_gradient(w, h, p['bgstops'], center=(0.5, 0.4))
    return diagonal_gradient(w, h, p['bgstops'], angle_deg=ang)


HERO_POSES = ['leap', 'stand_power', 'run']


def hero(p, idx=0):
    w, h = 1600, 1000
    im = make_bg(w, h, p)
    pose = HERO_POSES[idx % len(HERO_POSES)]
    im = add_rays(im, (0.52, 0.34), n=22, color=hex2rgb_safe(p['pal'].accent2), alpha=32)
    im = draw_energy_rings(im, (0.52, 0.72), hex2rgb_safe(p['pal'].accent), n=2, base_r=0.16, gap=0.1, alpha=90)
    im = draw_hero_figure(im, p['pal'], origin=(0.52, 0.74), scale=1.05, pose=pose, facing=p['facing'])
    im = add_speed_lines(im, 'left' if p['facing'] > 0 else 'right', color=(255, 255, 255))
    im = draw_emblem(im, p['emblem'], (0.84 if p['facing'] > 0 else 0.16, 0.22), 190,
                      hex2rgb_safe(p['pal'].accent2), hex2rgb_safe(p['pal'].accent), rot=0.3, alpha=235)
    im = add_sparkles(im, rnd_seed=hash(p['slug']) % 999, n=24)
    im = halftone_overlay(im)
    im = vignette(im, 0.5)
    im = grain(im, 5)
    return im


def panel_a(p, idx=0):
    """close bust + impact burst"""
    w, h = 1200, 900
    im = make_bg(w, h, p, ang=95)
    pose = HERO_POSES[(idx + 1) % len(HERO_POSES)]
    im = impact_burst(im, (0.5, 0.4), color=hex2rgb_safe(p['pal'].accent2), n=14, r_out=0.42, alpha=110)
    im = draw_hero_figure(im, p['pal'], origin=(0.5, 0.92), scale=1.7, pose=pose, facing=p['facing'])
    im = add_sparkles(im, rnd_seed=hash(p['slug'] + 'a') % 999, n=18, region=(0, 0, 1, 0.6))
    im = halftone_overlay(im, region=(0, 0.5, 1, 1))
    im = vignette(im, 0.5)
    im = grain(im, 5)
    return im


def panel_b(p):
    """wide environment / emblem showcase, no figure"""
    w, h = 1400, 800
    im = make_bg(w, h, p, ang=60)
    im = add_rays(im, (0.5, 0.5), n=16, color=hex2rgb_safe(p['pal'].accent), alpha=26)
    for i, (ex, ey) in enumerate([(0.22, 0.32), (0.5, 0.55), (0.78, 0.3)]):
        s = [150, 230, 150][i]
        im = draw_emblem(im, p['emblem'], (ex, ey), s, hex2rgb_safe(p['pal'].accent),
                          hex2rgb_safe(p['pal'].accent2), rot=i * 0.6, alpha=225)
    im = add_speed_lines(im, 'left', color=(255, 255, 255), n=10, alpha=60)
    im = add_sparkles(im, rnd_seed=hash(p['slug'] + 'b') % 999, n=22)
    im = halftone_overlay(im)
    im = vignette(im, 0.45)
    im = grain(im, 5)
    return im


def panel_c(p, idx=0):
    """alt pose, energy rings, opposite facing energy"""
    w, h = 1200, 900
    im = make_bg(w, h, p, ang=145)
    pose = HERO_POSES[(idx + 2) % len(HERO_POSES)]
    im = draw_energy_rings(im, (0.5, 0.68), hex2rgb_safe(p['pal'].accent2), n=4, base_r=0.12, gap=0.08, alpha=120)
    im = draw_hero_figure(im, p['pal'], origin=(0.5, 0.76), scale=1.25, pose=pose, facing=-p['facing'])
    im = add_speed_lines(im, 'right' if p['facing'] > 0 else 'left', color=(255, 255, 255))
    im = add_sparkles(im, rnd_seed=hash(p['slug'] + 'c') % 999, n=16)
    im = halftone_overlay(im)
    im = vignette(im, 0.5)
    im = grain(im, 5)
    return im


def hex2rgb_safe(x):
    if isinstance(x, tuple):
        return x
    return hex2rgb(x)


def thumb(hero_im):
    w, h = 900, 600
    src_w, src_h = hero_im.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        crop = hero_im.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = int((src_h - new_h) * 0.35)
        crop = hero_im.crop((0, top, src_w, top + new_h))
    return crop.resize((w, h), Image.LANCZOS)


def run():
    for idx, p in enumerate(PAGES):
        d = os.path.join(OUT_ROOT, p['slug'], 'assets', 'img')
        os.makedirs(d, exist_ok=True)
        h_im = hero(p, idx)
        save_webp(h_im, os.path.join(d, 'hero.webp'), quality=84)
        save_webp(panel_a(p, idx), os.path.join(d, 'panel-a.webp'), quality=82)
        save_webp(panel_b(p), os.path.join(d, 'panel-b.webp'), quality=82)
        save_webp(panel_c(p, idx), os.path.join(d, 'panel-c.webp'), quality=82)
        save_webp(thumb(h_im), os.path.join(d, 'thumb.webp'), quality=84)
        sizes = {f: os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)}
        print(p['slug'], sizes)


if __name__ == '__main__':
    run()
