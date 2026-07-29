"""
Anime poster-style procedural art generator.
Pure PIL + numpy. No external image-gen backend was reachable in this
session (no Higgsfield MCP tool, no API key) so all artwork here is
generated algorithmically in a bold flat "anime key-visual poster" style:
radiant gradient skies, halftone shading, big color-blocked character
silhouettes in dynamic poses, speed lines, sparkles and impact bursts.
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

TAU = math.pi * 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- gradients
def radial_gradient(w, h, stops, center=(0.5, 0.38), radius=1.05, ang_bias=0.0):
    """stops: list of (pos0..1, hexcolor). ang_bias adds a slight sweep for energy."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = center[0] * w, center[1] * h
    dx = (xs - cx) / (max(w, h) * radius)
    dy = (ys - cy) / (max(w, h) * radius)
    d = np.sqrt(dx * dx + dy * dy)
    if ang_bias:
        ang = np.arctan2(dy, dx)
        d = d + ang_bias * np.sin(ang * 3.0) * 0.03
    d = np.clip(d, 0, 1)
    colors = [(p, np.array(hex2rgb(c), dtype=np.float32)) for p, c in stops]
    out = np.zeros((h, w, 3), dtype=np.float32)
    for i in range(len(colors) - 1):
        p0, c0 = colors[i]
        p1, c1 = colors[i + 1]
        mask = (d >= p0) & (d <= p1)
        t = np.clip((d - p0) / max(1e-6, (p1 - p0)), 0, 1)
        seg = c0[None, None, :] + (c1 - c0)[None, None, :] * t[:, :, None]
        out = np.where(mask[:, :, None], seg, out)
    out = np.where((d < colors[0][0])[:, :, None], colors[0][1][None, None, :], out)
    out = np.where((d > colors[-1][0])[:, :, None], colors[-1][1][None, None, :], out)
    return Image.fromarray(out.astype(np.uint8), 'RGB')


def diagonal_gradient(w, h, stops, angle_deg=115):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle_deg)
    proj = xs * math.cos(a) + ys * math.sin(a)
    proj -= proj.min()
    proj /= max(1e-6, proj.max())
    colors = [(p, np.array(hex2rgb(c), dtype=np.float32)) for p, c in stops]
    out = np.zeros((h, w, 3), dtype=np.float32)
    for i in range(len(colors) - 1):
        p0, c0 = colors[i]
        p1, c1 = colors[i + 1]
        mask = (proj >= p0) & (proj <= p1)
        t = np.clip((proj - p0) / max(1e-6, (p1 - p0)), 0, 1)
        seg = c0[None, None, :] + (c1 - c0)[None, None, :] * t[:, :, None]
        out = np.where(mask[:, :, None], seg, out)
    out = np.where((proj < colors[0][0])[:, :, None], colors[0][1][None, None, :], out)
    out = np.where((proj > colors[-1][0])[:, :, None], colors[-1][1][None, None, :], out)
    return Image.fromarray(out.astype(np.uint8), 'RGB')


# ---------------------------------------------------------------- fx layers
def add_rays(im, center, n=24, color=(255, 255, 255), alpha=60, spin=0.0, inner=0.08, outer=1.3, width_jitter=0.6):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center[0] * w, center[1] * h
    R = max(w, h) * outer
    for i in range(n):
        a0 = spin + i * TAU / n
        hw = (TAU / n) * 0.5 * (0.35 + width_jitter * ((i * 37) % 7) / 7)
        p1 = (cx + math.cos(a0 - hw) * R, cy + math.sin(a0 - hw) * R)
        p2 = (cx + math.cos(a0 + hw) * R, cy + math.sin(a0 + hw) * R)
        p0a = (cx + math.cos(a0 - hw) * R * inner, cy + math.sin(a0 - hw) * R * inner)
        p0b = (cx + math.cos(a0 + hw) * R * inner, cy + math.sin(a0 + hw) * R * inner)
        if i % 2 == 0:
            d.polygon([p0a, p1, p2, p0b], fill=(*color, alpha))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def add_speed_lines(im, side='left', color=(255, 255, 255), n=14, alpha=90, band=(0.0, 0.55)):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(42)
    x0 = -w * 0.1 if side == 'left' else w * 1.1
    x1lo, x1hi = (w * band[0], w * band[1]) if side == 'left' else (w * (1 - band[1]), w * (1 - band[0]))
    for i in range(n):
        y = rnd.uniform(0.03, 0.97) * h
        length = rnd.uniform(0.15, 0.42) * w
        thick = rnd.uniform(2, 7)
        x1 = x0 + length if side == 'left' else x0 - length
        a = alpha * rnd.uniform(0.4, 1.0)
        d.line([(x0, y), (x1, y + rnd.uniform(-14, 14))], fill=(*color, int(a)), width=int(thick))
    layer = layer.filter(ImageFilter.GaussianBlur(0.6))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def add_sparkles(im, rnd_seed=1, n=26, colors=((255, 255, 255), (255, 240, 160)), region=(0, 0, 1, 1), size_range=(6, 26)):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(rnd_seed)
    for i in range(n):
        x = rnd.uniform(region[0], region[2]) * w
        y = rnd.uniform(region[1], region[3]) * h
        s = rnd.uniform(*size_range)
        c = rnd.choice(colors)
        a = rnd.randint(120, 235)
        _draw_star4(d, (x, y), s, (*c, a))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def _draw_star4(d, center, size, fill):
    cx, cy = center
    pts = []
    for k in range(8):
        ang = k * TAU / 8
        r = size if k % 2 == 0 else size * 0.28
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    d.polygon(pts, fill=fill)


def halftone_overlay(im, cell=10, color=(0, 0, 0), max_alpha=70, region=(0.0, 0.55, 1.0, 1.0)):
    """Subtle dot-screen shading in the lower region for print-anime texture."""
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y0, y1 = int(region[1] * h), int(region[3] * h)
    x0, x1 = int(region[0] * w), int(region[2] * w)
    for y in range(y0, y1, cell):
        t = (y - y0) / max(1, (y1 - y0))
        r = 1 + t * (cell * 0.42)
        a = int(max_alpha * t)
        off = (cell // 2) if ((y // cell) % 2) else 0
        for x in range(x0 - off, x1, cell):
            d.ellipse([x - r, y - r, x + r, y + r], fill=(*color, a))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def vignette(im, strength=0.55):
    w, h = im.size
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (xs - w / 2) / (w / 2)
    dy = (ys - h / 2) / (h / 2)
    d = np.sqrt(dx * dx + dy * dy)
    m = np.clip(1 - strength * np.clip(d - 0.55, 0, 1), 0, 1)
    arr = np.asarray(im).astype(np.float32)
    arr = arr * m[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')


def impact_burst(im, center, color=(255, 255, 255), n=16, r_in=0.02, r_out=0.5, alpha=230):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center[0] * w, center[1] * h
    R = max(w, h)
    for i in range(n):
        a0 = i * TAU / n
        hw = (TAU / n) * 0.28
        p1 = (cx + math.cos(a0 - hw) * R * r_out, cy + math.sin(a0 - hw) * R * r_out)
        p2 = (cx + math.cos(a0 + hw) * R * r_out, cy + math.sin(a0 + hw) * R * r_out)
        tip = (cx + math.cos(a0) * R * r_out * 1.35, cy + math.sin(a0) * R * r_out * 1.35)
        base_a = (cx + math.cos(a0 - hw) * R * r_in, cy + math.sin(a0 - hw) * R * r_in)
        base_b = (cx + math.cos(a0 + hw) * R * r_in, cy + math.sin(a0 + hw) * R * r_in)
        d.polygon([base_a, p1, tip, p2, base_b], fill=(*color, alpha))
    d.ellipse([cx - R * r_in * 2.2, cy - R * r_in * 2.2, cx + R * r_in * 2.2, cy + R * r_in * 2.2], fill=(*color, alpha))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def grain(im, amount=6, seed=7):
    arr = np.asarray(im).astype(np.int16)
    rnd = np.random.RandomState(seed)
    noise = rnd.randint(-amount, amount + 1, arr.shape[:2])[:, :, None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGB')


# ---------------------------------------------------------------- character
class Palette:
    def __init__(self, bg_far, bg_mid, bg_near, accent, accent2, skin, hair, outfit1, outfit2, rim):
        self.bg_far, self.bg_mid, self.bg_near = bg_far, bg_mid, bg_near
        self.accent, self.accent2 = accent, accent2
        self.skin, self.hair = skin, hair
        self.outfit1, self.outfit2 = outfit1, outfit2
        self.rim = rim


def _capsule(d, p1, p2, r1, r2, fill):
    x1, y1 = p1
    x2, y2 = p2
    ang = math.atan2(y2 - y1, x2 - x1)
    perp = ang + math.pi / 2
    pts = [
        (x1 + math.cos(perp) * r1, y1 + math.sin(perp) * r1),
        (x2 + math.cos(perp) * r2, y2 + math.sin(perp) * r2),
        (x2 - math.cos(perp) * r2, y2 - math.sin(perp) * r2),
        (x1 - math.cos(perp) * r1, y1 - math.sin(perp) * r1),
    ]
    d.polygon(pts, fill=fill)
    d.ellipse([x1 - r1, y1 - r1, x1 + r1, y1 + r1], fill=fill)
    d.ellipse([x2 - r2, y2 - r2, x2 + r2, y2 + r2], fill=fill)


def draw_hero_figure(im, pal: Palette, origin=(0.5, 0.72), scale=1.0, pose='leap',
                      spike_hair=True, rim_light=True, facing=1, power=1.0):
    """A bold, flat color-blocked dynamic anime hero silhouette (stylized, not literal anatomy)."""
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = origin[0] * w, origin[1] * h
    S = min(w, h) * 0.62 * scale
    fx = facing

    hip = (ox, oy)
    if pose == 'leap':
        shoulder = (ox - 0.02 * S * fx, oy - 0.62 * S)
        head_c = (ox - 0.03 * S * fx, oy - 0.82 * S)
        hand_l = (ox - 0.5 * S * fx, oy - 0.95 * S)
        hand_r = (ox + 0.42 * S * fx, oy - 0.35 * S)
        foot_l = (ox - 0.32 * S * fx, oy + 0.42 * S)
        foot_r = (ox + 0.4 * S * fx, oy + 0.5 * S)
        knee_l = (ox - 0.28 * S * fx, oy + 0.12 * S)
        knee_r = (ox + 0.3 * S * fx, oy + 0.16 * S)
        elbow_l = (ox - 0.42 * S * fx, oy - 0.72 * S)
        elbow_r = (ox + 0.32 * S * fx, oy - 0.5 * S)
    elif pose == 'stand_power':
        shoulder = (ox, oy - 0.66 * S)
        head_c = (ox, oy - 0.86 * S)
        hand_l = (ox - 0.46 * S, oy - 0.98 * S)
        hand_r = (ox + 0.46 * S, oy - 0.98 * S)
        foot_l = (ox - 0.2 * S, oy + 0.55 * S)
        foot_r = (ox + 0.2 * S, oy + 0.55 * S)
        knee_l = (ox - 0.2 * S, oy + 0.2 * S)
        knee_r = (ox + 0.2 * S, oy + 0.2 * S)
        elbow_l = (ox - 0.44 * S, oy - 0.78 * S)
        elbow_r = (ox + 0.44 * S, oy - 0.78 * S)
    else:  # 'run'
        shoulder = (ox - 0.02 * S * fx, oy - 0.6 * S)
        head_c = (ox + 0.02 * S * fx, oy - 0.8 * S)
        hand_l = (ox - 0.46 * S * fx, oy - 0.5 * S)
        hand_r = (ox + 0.4 * S * fx, oy - 0.72 * S)
        foot_l = (ox - 0.44 * S * fx, oy + 0.5 * S)
        foot_r = (ox + 0.3 * S * fx, oy + 0.4 * S)
        knee_l = (ox - 0.3 * S * fx, oy + 0.14 * S)
        knee_r = (ox + 0.22 * S * fx, oy + 0.05 * S)
        elbow_l = (ox - 0.38 * S * fx, oy - 0.6 * S)
        elbow_r = (ox + 0.34 * S * fx, oy - 0.66 * S)

    leg_r = S * 0.09
    d.polygon([hip, knee_r, foot_r, (hip[0] + S * 0.1, hip[1])], fill=pal.outfit2)
    _capsule(d, hip, knee_r, leg_r, leg_r * 0.8, pal.outfit2)
    _capsule(d, knee_r, foot_r, leg_r * 0.8, leg_r * 0.55, pal.outfit2)
    _capsule(d, hip, knee_l, leg_r, leg_r * 0.8, pal.outfit1)
    _capsule(d, knee_l, foot_l, leg_r * 0.8, leg_r * 0.55, pal.outfit1)

    torso_r1, torso_r2 = S * 0.155, S * 0.185
    neck = (lerp(hip[0], shoulder[0], 0.92), lerp(hip[1], shoulder[1], 0.92))
    _capsule(d, hip, neck, torso_r1, torso_r2, pal.outfit1)

    arm_r = S * 0.075
    _capsule(d, shoulder, elbow_r, arm_r, arm_r * 0.85, pal.outfit2)
    _capsule(d, elbow_r, hand_r, arm_r * 0.85, arm_r * 0.6, pal.skin)
    _capsule(d, shoulder, elbow_l, arm_r, arm_r * 0.85, pal.outfit1)
    _capsule(d, elbow_l, hand_l, arm_r * 0.85, arm_r * 0.6, pal.skin)

    if rim_light:
        for p1, p2, rr in [(hip, shoulder, torso_r1), (shoulder, elbow_r, arm_r), (elbow_r, hand_r, arm_r * 0.7)]:
            x1, y1 = p1
            x2, y2 = p2
            ang = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
            d.line([(x1 + math.cos(ang) * rr, y1 + math.sin(ang) * rr),
                    (x2 + math.cos(ang) * rr, y2 + math.sin(ang) * rr)], fill=(*pal.rim, 210), width=max(2, int(S * 0.012)))

    head_r = S * 0.155
    if spike_hair:
        n_spikes = 7
        for i in range(n_spikes):
            t = i / (n_spikes - 1)
            base_ang = math.radians(lerp(-170, -10, t)) if fx > 0 else math.radians(lerp(-10, -170, t))
            bx = head_c[0] + math.cos(base_ang) * head_r * 0.95
            by = head_c[1] + math.sin(base_ang) * head_r * 0.95
            spike_len = head_r * (1.5 + 0.9 * abs(math.sin(i * 2.1)))
            tipx = head_c[0] + math.cos(base_ang) * (head_r + spike_len)
            tipy = head_c[1] + math.sin(base_ang) * (head_r + spike_len) - head_r * 0.5
            side_ang = base_ang + math.pi / 2
            w1 = head_r * 0.32
            p_a = (bx + math.cos(side_ang) * w1, by + math.sin(side_ang) * w1)
            p_b = (bx - math.cos(side_ang) * w1, by - math.sin(side_ang) * w1)
            d.polygon([p_a, (tipx, tipy), p_b], fill=pal.hair)
    d.ellipse([head_c[0] - head_r, head_c[1] - head_r, head_c[0] + head_r, head_c[1] + head_r], fill=pal.skin)
    hair_band = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    hb = ImageDraw.Draw(hair_band)
    hb.pieslice([head_c[0] - head_r, head_c[1] - head_r, head_c[0] + head_r, head_c[1] + head_r],
                180, 360, fill=pal.hair)
    layer = Image.alpha_composite(layer, hair_band)
    d = ImageDraw.Draw(layer)

    er = head_r * 0.11
    ex = head_c[0] + fx * head_r * 0.32
    d.ellipse([ex - er, head_c[1] - er, ex + er, head_c[1] + er], fill=(20, 18, 30, 255))

    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def draw_energy_rings(im, center, color, n=3, base_r=0.18, gap=0.09, alpha=140, width=8):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center[0] * w, center[1] * h
    for i in range(n):
        r = (base_r + gap * i) * max(w, h)
        bbox = [cx - r, cy - r * 0.5, cx + r, cy + r * 0.5]
        d.ellipse(bbox, outline=(*color, max(10, alpha - i * 30)), width=width)
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im


def framed(im, border=10, color=(20, 16, 30)):
    w, h = im.size
    out = Image.new('RGB', (w, h), color)
    inner = im.resize((w - border * 2, h - border * 2))
    out.paste(inner, (border, border))
    return out


def save_webp(im, path, quality=82, method=6):
    im.save(path, 'WEBP', quality=quality, method=method)


def canvas(w, h):
    return Image.new('RGB', (w, h), (0, 0, 0))


# ---------------------------------------------------------------- emblems
def draw_emblem(im, kind, center, size, c1, c2, rot=0.0, alpha=255):
    w, h = im.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center[0] * w, center[1] * h
    S = size

    def rp(pts):
        out = []
        for (x, y) in pts:
            rx = x * math.cos(rot) - y * math.sin(rot)
            ry = x * math.sin(rot) + y * math.cos(rot)
            out.append((cx + rx, cy + ry))
        return out

    if kind == 'bolt':
        pts = rp([(-0.15, -0.5), (0.12, -0.05), (-0.05, -0.05), (0.15, 0.5), (-0.12, 0.05), (0.05, 0.05)])
        d.polygon([(cx + x * S, cy + y * S) for x, y in [( -0.15,-0.5),(0.12,-0.05),(-0.05,-0.05),(0.15,0.5),(-0.12,0.05),(0.05,0.05)]], fill=(*c1, alpha))
    elif kind == 'wave':
        pts = []
        for i in range(0, 21):
            t = i / 20
            x = (t - 0.5) * S
            y = math.sin(t * TAU * 1.5 + rot) * S * 0.14
            pts.append((cx + x, cy + y))
        d.line(pts, fill=(*c1, alpha), width=max(3, int(S * 0.05)), joint='curve')
        pts2 = [(x, y + S * 0.18) for x, y in pts]
        d.line(pts2, fill=(*c2, alpha), width=max(3, int(S * 0.035)), joint='curve')
    elif kind == 'gear':
        teeth = 10
        for i in range(teeth):
            a = i * TAU / teeth
            p1 = (cx + math.cos(a) * S * 0.42, cy + math.sin(a) * S * 0.42)
            p2 = (cx + math.cos(a + 0.12) * S * 0.62, cy + math.sin(a + 0.12) * S * 0.62)
            p3 = (cx + math.cos(a + 0.24) * S * 0.42, cy + math.sin(a + 0.24) * S * 0.42)
            d.polygon([p1, p2, p3, (cx, cy)], fill=(*c1, alpha))
        d.ellipse([cx - S * 0.42, cy - S * 0.42, cx + S * 0.42, cy + S * 0.42], fill=(*c1, alpha))
        d.ellipse([cx - S * 0.18, cy - S * 0.18, cx + S * 0.18, cy + S * 0.18], fill=(*c2, alpha))
    elif kind == 'bottle':
        d.rounded_rectangle([cx - S * 0.22, cy - S * 0.1, cx + S * 0.22, cy + S * 0.55], radius=S * 0.12, fill=(*c1, alpha))
        d.rectangle([cx - S * 0.09, cy - S * 0.42, cx + S * 0.09, cy - S * 0.05], fill=(*c1, alpha))
        d.rounded_rectangle([cx - S * 0.12, cy - S * 0.55, cx + S * 0.12, cy - S * 0.4], radius=S * 0.05, fill=(*c2, alpha))
        d.ellipse([cx - S * 0.18, cy + S * 0.15, cx + S * 0.18, cy + S * 0.48], fill=(*c2, int(alpha * 0.85)))
    elif kind == 'note':
        d.ellipse([cx - S * 0.16, cy + S * 0.28, cx + S * 0.16, cy + S * 0.5], fill=(*c1, alpha))
        d.rectangle([cx + S * 0.14, cy - S * 0.5, cx + S * 0.2, cy + S * 0.4], fill=(*c1, alpha))
        d.polygon([(cx + S * 0.14, cy - S * 0.5), (cx + S * 0.46, cy - S * 0.4), (cx + S * 0.46, cy - S * 0.18), (cx + S * 0.14, cy - S * 0.28)], fill=(*c2, alpha))
    elif kind == 'ball':
        d.ellipse([cx - S * 0.42, cy - S * 0.42, cx + S * 0.42, cy + S * 0.42], fill=(*c1, alpha))
        d.arc([cx - S * 0.42, cy - S * 0.42, cx + S * 0.42, cy + S * 0.42], 20, 160, fill=(*c2, alpha), width=max(3, int(S * 0.03)))
        d.line([(cx, cy - S * 0.42), (cx, cy + S * 0.42)], fill=(*c2, alpha), width=max(3, int(S * 0.03)))
    elif kind == 'planet':
        d.ellipse([cx - S * 0.3, cy - S * 0.3, cx + S * 0.3, cy + S * 0.3], fill=(*c1, alpha))
        d.ellipse([cx - S * 0.55, cy - S * 0.12, cx + S * 0.55, cy + S * 0.12], outline=(*c2, alpha), width=max(3, int(S * 0.045)))
    elif kind == 'blade':
        pts = rp([(0, -0.55), (0.09, -0.1), (0.05, 0.5), (-0.05, 0.5), (-0.09, -0.1)])
        d.polygon(pts, fill=(*c1, alpha))
        pts2 = rp([(-0.03, 0.5), (0.03, 0.5), (0.03, 0.65), (-0.03, 0.65)])
        d.polygon(pts2, fill=(*c2, alpha))
    elif kind == 'pixel':
        n = 4
        cell = S * 0.22
        rnd = random.Random(int(S) + int(cx))
        for gy in range(n):
            for gx in range(n):
                if rnd.random() > 0.45:
                    x0 = cx - n * cell / 2 + gx * cell
                    y0 = cy - n * cell / 2 + gy * cell
                    d.rectangle([x0, y0, x0 + cell * 0.9, y0 + cell * 0.9], fill=(*(c1 if (gx + gy) % 2 else c2), alpha))
    elif kind == 'flower':
        petals = 5
        for i in range(petals):
            a = i * TAU / petals + rot
            px = cx + math.cos(a) * S * 0.28
            py = cy + math.sin(a) * S * 0.28
            d.ellipse([px - S * 0.2, py - S * 0.2, px + S * 0.2, py + S * 0.2], fill=(*c1, alpha))
        d.ellipse([cx - S * 0.15, cy - S * 0.15, cx + S * 0.15, cy + S * 0.15], fill=(*c2, alpha))
    im.paste(Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB'), (0, 0))
    return im
