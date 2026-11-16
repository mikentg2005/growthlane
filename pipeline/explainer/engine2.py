"""Explainer-video engine v2: camera, flat-design characters, rooms, props, effects.

Everything is drawn with Pillow at 2x and reduced (smooth edges). World coordinates are
the 1080x1920 frame; the camera (cx, cy, zoom) maps world -> screen, and c.hud() draws
without the camera (titles, captions). No external assets or paid tools.
"""
import math
import random
import subprocess
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SS = 1080, 1920, 30, 2
FONTS = Path("C:/Windows/Fonts")

# palette
PAPER, INK, MUTED, GREEN = (247, 245, 238), (23, 32, 27), (86, 99, 91), (29, 95, 74)
WARN, WARN_SOFT, GREEN_SOFT, LINE = (190, 80, 45), (243, 228, 220), (227, 238, 232), (218, 214, 200)
GOLD, SKY, SKY2, WHITE = (240, 184, 60), (150, 205, 235), (214, 236, 247), (255, 255, 255)
WALL, WALL2, FLOOR, WOOD, WOOD2 = (246, 226, 205), (236, 208, 184), (190, 150, 116), (176, 128, 86), (140, 98, 64)


# ---------- helpers ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def out_back(u, s=1.70158):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


def out_elastic(u):
    u = clamp(u)
    if u in (0, 1):
        return u
    return 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * (2 * math.pi) / 3) + 1


def out_cubic(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def mix(c1, c2, u):
    u = clamp(u)
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def prog(t, t0, dur, fn=ease):
    return fn((t - t0) / dur)


@lru_cache(maxsize=256)
def _font(name, px):
    path = {"head": "GeorgiaPro-Bold.ttf", "bold": "arialbd.ttf", "text": "arial.ttf", "hand": "Inkfree.ttf", "handb": "segoeprb.ttf"}[name]
    return ImageFont.truetype(str(FONTS / path), max(6, int(px)))


@lru_cache(maxsize=16)
def gradient(top, bottom, h=H, w=W):
    t = np.array(top, dtype=np.float32)
    b = np.array(bottom, dtype=np.float32)
    u = np.linspace(0, 1, h * SS, dtype=np.float32)[:, None, None]
    arr = (t * (1 - u) + b * u).astype(np.uint8)
    arr = np.repeat(arr, w * SS, axis=1)
    return Image.fromarray(arr, "RGB")


@lru_cache(maxsize=64)
def glow_sprite(r, color):
    size = int(r * 2 * SS)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - d, 0, 1) ** 2
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


class Canvas:
    def __init__(self, bg=None):
        if bg is None:
            self.img = Image.new("RGB", (W * SS, H * SS), PAPER)
        else:
            self.img = bg.copy()
        self.d = ImageDraw.Draw(self.img)
        self.cx, self.cy, self.z = W / 2, H / 2, 1.0

    # camera
    def cam(self, cx=W / 2, cy=H / 2, z=1.0):
        self.cx, self.cy, self.z = cx, cy, z

    @contextmanager
    def hud(self):
        old = (self.cx, self.cy, self.z)
        self.cx, self.cy, self.z = W / 2, H / 2, 1.0
        yield
        self.cx, self.cy, self.z = old

    def X(self, x):
        return ((x - self.cx) * self.z + W / 2) * SS

    def Y(self, y):
        return ((y - self.cy) * self.z + H / 2) * SS

    def L(self, v):
        return v * self.z * SS

    def P(self, pts):
        return [(self.X(x), self.Y(y)) for x, y in pts]

    # primitives
    def line(self, pts, w, color, cap=True):
        p = self.P(pts)
        wd = max(1, int(self.L(w)))
        self.d.line(p, fill=color, width=wd, joint="curve")
        if cap:
            r = wd / 2
            for x, y in p:
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def circle(self, x, y, r, fill=None, outline=None, w=0):
        X, Y, R = self.X(x), self.Y(y), max(0.0, self.L(r))
        self.d.ellipse([X - R, Y - R, X + R, Y + R], fill=fill, outline=outline, width=int(self.L(w)))

    def ellipse(self, x, y, rx, ry, fill=None, outline=None, w=0):
        X, Y = self.X(x), self.Y(y)
        rx, ry = max(0.0, rx), max(0.0, ry)
        self.d.ellipse([X - self.L(rx), Y - self.L(ry), X + self.L(rx), Y + self.L(ry)],
                       fill=fill, outline=outline, width=int(self.L(w)))

    def rrect(self, x0, y0, x1, y1, r=0, fill=None, outline=None, w=0):
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        self.d.rounded_rectangle([self.X(x0), self.Y(y0), self.X(x1), self.Y(y1)], radius=max(0.0, self.L(r)),
                                 fill=fill, outline=outline, width=int(self.L(w)))

    def shadow(self, x, y, rx, ry, blur=14, opacity=0.16, color=(40, 32, 20)):
        """A soft blurred ellipse shadow centered at (x, y), to ground a character or object
        on the page. Draw this before the thing that casts it."""
        X, Y, RX, RY = self.X(x), self.Y(y), max(1.0, self.L(rx)), max(1.0, self.L(ry))
        pad = blur * self.z * SS * 2.2
        w, h = int(RX * 2 + pad * 2), int(RY * 2 + pad * 2)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([pad, pad, w - pad, h - pad], fill=color + (int(255 * opacity),))
        layer = layer.filter(ImageFilter.GaussianBlur(blur * self.z * SS))
        self.img.paste(layer, (int(X - w / 2), int(Y - h / 2)), layer)

    def poly(self, pts, fill=None, outline=None, w=0):
        self.d.polygon(self.P(pts), fill=fill, outline=outline, width=int(self.L(w)))

    def arc(self, x, y, r, a0, a1, w, color):
        X, Y, R = self.X(x), self.Y(y), max(0.0, self.L(r))
        self.d.arc([X - R, Y - R, X + R, Y + R], a0, a1, fill=color, width=max(1, int(self.L(w))))

    def pie(self, x, y, r, a0, a1, fill):
        X, Y, R = self.X(x), self.Y(y), max(0.0, self.L(r))
        self.d.pieslice([X - R, Y - R, X + R, Y + R], a0, a1, fill=fill)

    def text(self, s, x, y, name, size, color=INK, anchor="mm"):
        f = _font(name, size * self.z * SS)
        self.d.text((self.X(x), self.Y(y)), s, font=f, fill=color, anchor=anchor)

    def tw(self, s, name, size):
        return self.d.textlength(s, font=_font(name, size * SS)) / SS

    def glow(self, x, y, r, color, alpha=1.0):
        spr = glow_sprite(int(r), color)
        size = int(self.L(r) * 2)
        if size < 4:
            return
        sp = spr.resize((size, size))
        if alpha < 1:
            a = sp.getchannel("A").point(lambda v: int(v * alpha))
            sp.putalpha(a)
        self.img.paste(sp, (int(self.X(x) - size / 2), int(self.Y(y) - size / 2)), sp)

    def wrap(self, s, name, size, width):
        lines, cur = [], ""
        for w in s.split():
            t = (cur + " " + w).strip()
            if self.tw(t, name, size) <= width:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def words(self, s, x, y, name, size, width, t, t0, color=INK, lh=1.3, per=0.07, hi=None):
        """HUD text: words pop in one after another. hi = {word: colour} highlights."""
        n = 0
        with self.hud():
            for line in self.wrap(s, name, size, width):
                ws = line.split()
                total = self.tw(line, name, size)
                cx = x - total / 2
                sp = self.tw(" ", name, size)
                for w in ws:
                    a = clamp((t - t0 - n * per) / 0.22)
                    if a > 0:
                        col = (hi or {}).get(w.strip(".,!?:;"), color)
                        off = (1 - out_back(a)) * 26
                        self.text(w, cx, y - off, name, size * (0.85 + 0.15 * out_back(a)), mix(PAPER, col, a), "lm")
                    cx += self.tw(w, name, size) + sp
                    n += 1
                y += size * lh
        return n * per + 0.22

    def frame(self):
        return self.img.reduce(SS)


# ---------- characters ----------
class Look:
    def __init__(self, skin=(240, 196, 160), hair=(70, 48, 36), shirt=GREEN, pants=(52, 66, 92),
                 shoes=(30, 34, 40), style="short"):
        self.skin, self.hair, self.shirt, self.pants, self.shoes, self.style = skin, hair, shirt, pants, shoes, style


ALEX = Look()
SAM = Look(skin=(214, 160, 120), hair=(36, 28, 24), shirt=(222, 120, 70), pants=(80, 80, 96), style="bun")
FUTURE = Look(skin=(240, 196, 160), hair=(70, 48, 36), shirt=(60, 130, 200), pants=(52, 66, 92))

# degrees from straight down; 90 = toward the front, 180 = up. Pairs: (limb angle, bend relative)
POSES = {
    "stand":  dict(lean=0, tilt=0, af=(12, 6), ab=(-12, -6), lf=(5, 0), lb=(-5, 0), brow=0, mouth="smile"),
    "slump":  dict(lean=12, tilt=16, af=(6, 4), ab=(-4, -2), lf=(8, 0), lb=(-4, 0), brow=0.7, mouth="sad"),
    "shrug":  dict(lean=0, tilt=8, af=(60, 70), ab=(-60, -70), lf=(5, 0), lb=(-5, 0), brow=0.5, mouth="flat"),
    "worry":  dict(lean=4, tilt=10, af=(150, -118), ab=(-8, -4), lf=(5, 0), lb=(-5, 0), brow=0.8, mouth="o"),
    "reach":  dict(lean=6, tilt=-4, af=(98, 4), ab=(-24, -10), lf=(10, 0), lb=(-10, 0), brow=-0.1, mouth="grin"),
    "cheer":  dict(lean=-2, tilt=-6, af=(128, 40), ab=(-128, -40), lf=(10, 0), lb=(-10, 0), brow=-0.2, mouth="grin"),
    "sit":    dict(lean=0, tilt=0, af=(54, 40), ab=(44, 36), lf=(92, -92), lb=(86, -88), brow=0.2, mouth="flat"),
    "sitlook": dict(lean=-4, tilt=-20, af=(54, 40), ab=(44, 36), lf=(92, -92), lb=(86, -88), brow=0.4, mouth="o"),
    "sitphone": dict(lean=-2, tilt=-12, af=(66, 66), ab=(44, 36), lf=(92, -92), lb=(86, -88), brow=0.2, mouth="flat"),
    "type":   dict(lean=2, tilt=4, af=(60, 36), ab=(50, 40), lf=(92, -92), lb=(86, -88), brow=-0.3, mouth="grin"),
    "walkA":  dict(lean=4, tilt=0, af=(40, 20), ab=(-40, -20), lf=(34, -14), lb=(-30, -6), brow=0, mouth="smile"),
    "walkB":  dict(lean=4, tilt=0, af=(-40, -20), ab=(40, 20), lf=(-30, -6), lb=(34, -14), brow=0, mouth="smile"),
    "wave":   dict(lean=0, tilt=-4, af=(150, -20), ab=(-12, -6), lf=(5, 0), lb=(-5, 0), brow=-0.1, mouth="grin"),
    "point":  dict(lean=4, tilt=-2, af=(100, 2), ab=(-10, -6), lf=(8, 0), lb=(-8, 0), brow=-0.1, mouth="smile"),
    "scared": dict(lean=-6, tilt=-10, af=(100, 60), ab=(-60, -50), lf=(14, 0), lb=(-12, 0), brow=1.0, mouth="o"),
}
TORSO, NECK, HEADR, UA, FA, TH, SH = 140, 16, 50, 62, 58, 84, 82


def get_pose(p):
    return POSES[p] if isinstance(p, str) else p


def pose_mix(a, b, u):
    a, b = get_pose(a), get_pose(b)
    out = {}
    for k in a:
        if k == "mouth":
            out[k] = a[k] if u < 0.5 else b[k]
        elif isinstance(a[k], tuple):
            out[k] = tuple(lerp(x, y, u) for x, y in zip(a[k], b[k]))
        else:
            out[k] = lerp(a[k], b[k], u)
    return out


def dirv(deg):
    r = math.radians(deg)
    return math.sin(r), math.cos(r)


def draw_person(c, x, y, pose, look=ALEX, scale=1.0, flip=False, t=0.0, gaze=(1.0, 0.0), shadow=None,
                eyes="normal"):
    """Hip at (x, y). Returns dict of key points (head, hand, top)."""
    p = dict(get_pose(pose))
    m = -1 if flip else 1
    k = scale
    breathe = math.sin(t * 2.4) * 1.6
    p["lean"] += breathe * 0.5
    if shadow is not None:
        c.ellipse(x + m * 6 * k, y + (TH + SH) * k * (1 if p["lf"][0] < 60 else 0.5) + 2, 90 * k, 12 * k, fill=shadow)

    def limb(origin, a1, a2, l1, l2):
        d1 = dirv(a1)
        j = (origin[0] + m * d1[0] * l1 * k, origin[1] + d1[1] * l1 * k)
        d2 = dirv(a1 + a2)
        e = (j[0] + m * d2[0] * l2 * k, j[1] + d2[1] * l2 * k)
        return j, e

    hip = (x, y)
    lean = math.radians(p["lean"])
    top = (x + m * math.sin(lean) * TORSO * k, y - math.cos(lean) * TORSO * k + breathe * k)
    leg_w, torso_w = 30 * k, 66 * k
    dark = tuple(int(v * 0.82) for v in look.pants)
    # back leg, back arm
    j, e = limb(hip, *p["lb"], TH, SH)
    c.line([hip, j, e], leg_w, dark)
    c.ellipse(e[0] + m * 12 * k, e[1] + 6 * k, 20 * k, 9 * k, fill=look.shoes)
    j2, e2 = limb(top, *p["ab"], UA, FA)
    c.line([top, j2], 24 * k, tuple(int(v * 0.85) for v in look.shirt))
    c.line([j2, e2], 19 * k, tuple(int(v * 0.88) for v in look.skin))
    c.circle(e2[0], e2[1], 11 * k, fill=tuple(int(v * 0.88) for v in look.skin))
    # front leg
    j, e = limb(hip, *p["lf"], TH, SH)
    c.line([hip, j, e], leg_w, look.pants)
    c.ellipse(e[0] + m * 12 * k, e[1] + 6 * k, 20 * k, 9 * k, fill=look.shoes)
    # torso
    c.line([(hip[0], hip[1] + 6 * k), top], torso_w, look.shirt)
    # neck + head
    tilt = math.radians(p["tilt"])
    hc = (top[0] + m * math.sin(tilt) * (NECK + HEADR) * k, top[1] - math.cos(tilt) * (NECK + HEADR) * k)
    c.line([top, hc], 20 * k, look.skin)
    r = HEADR * k
    c.circle(hc[0], hc[1], r, fill=look.skin)
    # hair
    if look.style == "bun":
        c.circle(hc[0] - m * r * 0.75, hc[1] - r * 0.85, r * 0.36, fill=look.hair)
    c.circle(hc[0] - m * r * 0.82, hc[1] - r * 0.05, r * 0.26, fill=look.hair)
    c.pie(hc[0], hc[1], r * 1.04, 198, 342, look.hair)
    c.pie(hc[0] - m * r * 0.1, hc[1] - r * 0.1, r * 1.0, 180, 360, look.hair) if False else None
    # face
    blink = (t % 3.4) < 0.12
    gx, gy = gaze
    for sx in (0.28, 0.78):
        ex, ey = hc[0] + m * r * sx, hc[1] - r * 0.05
        if blink:
            c.line([(ex - r * 0.13, ey), (ex + r * 0.13, ey)], 3.5 * k, INK)
        elif eyes == "stars":
            for ang in (0, 45, 90, 135):
                dx, dy = math.cos(math.radians(ang)) * r * 0.2, math.sin(math.radians(ang)) * r * 0.2
                c.line([(ex - dx, ey - dy), (ex + dx, ey + dy)], 4 * k, GOLD)
        else:
            c.circle(ex, ey, r * 0.17, fill=WHITE)
            c.circle(ex + m * gx * r * 0.07, ey + gy * r * 0.07, r * 0.09, fill=INK)
        b = p["brow"]
        d = 1 if sx < 0.5 else -1
        yo = -r * 0.30
        c.line([(ex - m * d * r * 0.17, ey + yo), (ex + m * d * r * 0.17, ey + yo - b * r * 0.14)], 4 * k, look.hair)
    mx, my = hc[0] + m * r * 0.52, hc[1] + r * 0.46
    mouth = p["mouth"]
    mw = max(3, 4 * k)
    if mouth == "smile":
        c.arc(mx, my - r * 0.16, r * 0.26, 25, 155, mw, INK)
    elif mouth == "grin":
        c.pie(mx, my - r * 0.05, r * 0.28, 0, 180, INK)
    elif mouth == "sad":
        c.arc(mx, my + r * 0.16, r * 0.24, 205, 335, mw, INK)
    elif mouth == "o":
        c.circle(mx, my, r * 0.11, fill=INK)
    else:
        c.line([(mx - r * 0.2, my), (mx + r * 0.2, my)], mw, INK)
    # front arm
    j3, e3 = limb(top, *p["af"], UA, FA)
    c.line([top, j3], 24 * k, look.shirt)
    c.line([j3, e3], 19 * k, look.skin)
    c.circle(e3[0], e3[1], 11 * k, fill=look.skin)
    return {"head": hc, "hand": e3, "top": top, "hip": hip}


# ---------- room and props ----------
def room(c, t, *, window=True, tint=None, floor_y=1270):
    """Back wall, window, floor. Static layers are baked by the caller via Canvas(bg=...)."""
    c.rrect(-600, -400, 1700, floor_y, 0, fill=tint or WALL)
    c.rrect(-600, floor_y - 120, 1700, floor_y, 0, fill=WALL2)  # wainscot
    c.rrect(-600, floor_y, 1700, 2600, 0, fill=FLOOR)
    for i in range(-6, 12):
        c.line([(i * 200 + 40, floor_y), (i * 200 - 80, 2600)], 4, tuple(int(v * 0.92) for v in FLOOR), cap=False)
    c.line([(-600, floor_y), (1700, floor_y)], 8, tuple(int(v * 0.8) for v in FLOOR))
    if window:
        win(c, 190, 640, 300, 360, t)


def win(c, x, y, w, h, t):
    c.rrect(x - 12, y - 12, x + w + 12, y + h + 12, 14, fill=(255, 255, 255))
    c.rrect(x, y, x + w, y + h, 6, fill=SKY2)
    c.rrect(x, y + h * 0.55, x + w, y + h, 6, fill=SKY)
    for i, (cx0, cy0, s) in enumerate(((60, 90, 1.0), (210, 150, 0.7))):
        cx = x + ((cx0 + t * 6 * (1 + i * 0.5)) % (w + 120)) - 40
        for dx, dy, r in ((0, 0, 24), (26, 6, 20), (-24, 8, 17), (6, -12, 18)):
            c.circle(cx + dx * s, y + cy0 + dy * s, r * s, fill=WHITE)
    c.line([(x + w / 2, y), (x + w / 2, y + h)], 8, (255, 255, 255))
    c.line([(x, y + h / 2), (x + w, y + h / 2)], 8, (255, 255, 255))


def wall_clock(c, x, y, r, t, fast=False):
    c.circle(x, y, r + 8, fill=WOOD2)
    c.circle(x, y, r, fill=WHITE)
    for i in range(12):
        a = math.radians(i * 30)
        c.line([(x + math.sin(a) * r * 0.82, y - math.cos(a) * r * 0.82), (x + math.sin(a) * r * 0.92, y - math.cos(a) * r * 0.92)], 3, INK, cap=False)
    sp = 3.0 if fast else 0.35
    ah = math.radians(t * 30 * sp / 6)
    am = math.radians(t * 360 * sp / 6)
    c.line([(x, y), (x + math.sin(ah) * r * 0.5, y - math.cos(ah) * r * 0.5)], 6, INK)
    c.line([(x, y), (x + math.sin(am) * r * 0.78, y - math.cos(am) * r * 0.78)], 4, INK)
    c.circle(x, y, 5, fill=WARN)


def wall_calendar(c, x, y, w, h, title, circled=None, flip=0.0):
    c.rrect(x + 6, y + 8, x + w + 6, y + h + 8, 8, fill=tuple(int(v * 0.85) for v in WALL))
    c.rrect(x, y, x + w, y + h, 8, fill=WHITE)
    c.rrect(x, y, x + w, y + h * 0.22, 8, fill=WARN)
    c.text(title, x + w / 2, y + h * 0.11, "bold", h * 0.12, WHITE)
    cols, rows = 7, 5
    gw, gh = w / cols, (h * 0.74) / rows
    n = 0
    for r in range(rows):
        for q in range(cols):
            n += 1
            if n > 30:
                break
            cx, cy = x + gw * (q + 0.5), y + h * 0.26 + gh * (r + 0.5)
            if circled == n:
                c.circle(cx, cy, gh * 0.46, outline=WARN, w=4)
            c.text(str(n), cx, cy, "text", gh * 0.44, INK if circled != n else WARN)


def desk(c, x0, x1, top, ground=1270):
    c.rrect(x0, top, x1, top + 26, 8, fill=WOOD)
    c.rrect(x0, top + 22, x1, top + 36, 4, fill=WOOD2)
    c.rrect(x0 + 26, top + 36, x0 + 46, ground, 4, fill=WOOD2)
    c.rrect(x1 - 46, top + 36, x1 - 26, ground, 4, fill=WOOD2)


def chair(c, x, seat_y, ground=1270):
    c.rrect(x - 78, seat_y + 4, x + 36, seat_y + 24, 10, fill=(70, 80, 96))
    c.rrect(x - 84, seat_y - 190, x - 62, seat_y + 12, 10, fill=(70, 80, 96))
    c.rrect(x - 52, seat_y + 24, x - 40, ground - 20, 4, fill=(50, 56, 66))
    c.ellipse(x - 46, ground - 10, 46, 10, fill=(50, 56, 66))


def laptop(c, x, top, screen=None, glow=0.0, t=0.0, lines=0):
    c.rrect(x - 110, top - 150, x + 110, top - 4, 12, fill=(60, 66, 74))
    c.rrect(x - 98, top - 138, x + 98, top - 16, 6, fill=(250, 250, 248))
    if screen == "blank":
        c.line([(x - 80, top - 118), (x - 20, top - 118)], 7, LINE)
        if int(t * 2) % 2 == 0:
            c.rrect(x - 80, top - 106, x - 76, top - 82, 1, fill=INK)
    elif screen == "typing":
        for i in range(lines):
            ww = 150 - (i % 3) * 30
            c.line([(x - 84, top - 124 + i * 15), (x - 84 + ww, top - 124 + i * 15)], 6, (110, 160, 200))
    c.rrect(x - 124, top - 6, x + 124, top + 4, 4, fill=(140, 146, 152))
    if glow:
        c.glow(x, top - 76, 220, (255, 255, 230), glow)


def phone(c, x, y, shake=0.0, face=False, scale=1.0, tilt=0.0):
    dx = math.sin(shake * 55) * 5 * scale if shake else 0
    k = scale
    c.rrect(x - 44 * k + dx, y - 80 * k, x + 44 * k + dx, y + 80 * k, 16 * k, fill=(30, 34, 40))
    sc = (90, 200, 220) if face else (200, 215, 208)
    c.rrect(x - 36 * k + dx, y - 70 * k, x + 36 * k + dx, y + 68 * k, 9 * k, fill=sc)
    if face:
        for sx in (-14, 14):
            c.circle(x + sx * k + dx, y - 14 * k, 8 * k, fill=WHITE)
            c.circle(x + sx * k + dx + 2, y - 12 * k, 4 * k, fill=INK)
        c.line([(x - 22 * k + dx, y - 34 * k), (x - 6 * k + dx, y - 28 * k)], 4 * k, INK)
        c.line([(x + 22 * k + dx, y - 34 * k), (x + 6 * k + dx, y - 28 * k)], 4 * k, INK)
        c.pie(x + dx, y + 18 * k, 24 * k, 0, 180, INK)
        c.rrect(x - 14 * k + dx, y + 20 * k, x + 14 * k + dx, y + 26 * k, 2, fill=WHITE)


def plant(c, x, y, t=0.0):
    c.rrect(x - 34, y - 70, x + 34, y, 8, fill=(200, 110, 80))
    for i, (a, l) in enumerate(((-30, 110), (0, 140), (28, 115), (-60, 70), (58, 75))):
        sway = math.sin(t * 1.4 + i) * 3
        ang = math.radians(a + sway)
        ex, ey = x + math.sin(ang) * l, y - 70 - math.cos(ang) * l
        c.line([(x, y - 70), (ex, ey)], 8, (70, 140, 90))
        c.circle(ex, ey, 22, fill=(86, 160, 104))


def lamp(c, x, y):
    c.rrect(x - 30, y - 8, x + 30, y, 4, fill=(60, 66, 74))
    c.line([(x, y - 8), (x - 20, y - 80), (x + 30, y - 140)], 8, (60, 66, 74))
    c.poly([(x + 6, y - 150), (x + 70, y - 140), (x + 58, y - 100), (x + 24, y - 116)], fill=GOLD)


def icon_check(c, x, y, r, color=GREEN):
    c.circle(x, y, r, fill=color)
    c.line([(x - r * 0.45, y), (x - r * 0.1, y + r * 0.36), (x + r * 0.5, y - r * 0.34)], r * 0.2, WHITE)


def icon_heart(c, x, y, r, color=WARN):
    c.circle(x - r * 0.5, y - r * 0.2, r * 0.58, fill=color)
    c.circle(x + r * 0.5, y - r * 0.2, r * 0.58, fill=color)
    c.poly([(x - r * 1.04, y - r * 0.05), (x + r * 1.04, y - r * 0.05), (x, y + r * 1.05)], fill=color)


def icon_bolt(c, x, y, r, color=GOLD):
    c.poly([(x + r * 0.2, y - r), (x - r * 0.7, y + r * 0.15), (x - r * 0.05, y + r * 0.15),
            (x - r * 0.25, y + r), (x + r * 0.7, y - r * 0.2), (x + r * 0.05, y - r * 0.2)], fill=color)


def icon_hourglass(c, x, y, r, color=WARN):
    c.line([(x - r * 0.7, y - r), (x + r * 0.7, y - r)], r * 0.14, INK)
    c.line([(x - r * 0.7, y + r), (x + r * 0.7, y + r)], r * 0.14, INK)
    c.poly([(x - r * 0.6, y - r), (x + r * 0.6, y - r), (x + r * 0.08, y), (x + r * 0.6, y + r), (x - r * 0.6, y + r), (x - r * 0.08, y)],
           fill=mix(WHITE, color, 0.25))
    c.poly([(x - r * 0.38, y + r), (x + r * 0.38, y + r), (x, y + r * 0.45)], fill=color)


def icon_star(c, x, y, r, color=GOLD, rot=0.0):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36 + rot)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    c.poly(pts, fill=color)


def pill(c, x, y, label, color=GREEN, size=34, a=1.0):
    with c.hud():
        wd = c.tw(label, "bold", size) + 64
        c.rrect(x - wd / 2, y - 36, x + wd / 2, y + 36, 36, fill=mix(PAPER, color, a))
        c.text(label, x, y, "bold", size, mix(PAPER, WHITE, a))


def speech(c, x, y, w, h, text, size=44, tail=None, thought=False, a=1.0, color=INK):
    if a <= 0:
        return
    fill = (255, 253, 248)
    c.rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 38, fill=fill, outline=INK, w=5)
    if tail:
        tx, ty = tail
        if thought:
            for i, rr in enumerate((18, 12, 8)):
                u = 0.35 + i * 0.27
                c.circle(lerp(x, tx, u), lerp(y + h / 2, ty, u), rr, fill=fill, outline=INK, w=4)
        else:
            c.poly([(x - 24, y + h / 2 - 4), (x + 24, y + h / 2 - 4), (tx, ty)], fill=fill)
            c.line([(x - 24, y + h / 2), (tx, ty), (x + 24, y + h / 2)], 5, INK)
            c.line([(x - 22, y + h / 2 - 2), (x + 22, y + h / 2 - 2)], 8, fill)
    c.text(text, x, y, "head", size, mix(fill, color, a))


def meter(c, x, y, level, label="MOTIVATION", h=420, w=70, a=1.0):
    with c.hud():
        c.text(label, x, y - 40, "bold", 24, mix(PAPER, MUTED, a))
        c.rrect(x - w / 2, y, x + w / 2, y + h, 24, fill=(236, 232, 220), outline=mix(PAPER, LINE, a), w=3)
        lv = clamp(level)
        col = mix(WARN, GREEN, ease((lv - 0.15) / 0.6))
        fh = max(w - 14, (h - 14) * lv)
        c.rrect(x - w / 2 + 7, y + h - 7 - fh, x + w / 2 - 7, y + h - 7, 17, fill=col)
        for q in (0.25, 0.5, 0.75):
            c.line([(x - w / 2 - 2, y + h * q), (x - w / 2 + 14, y + h * q)], 3, MUTED, cap=False)


def confetti(c, t, t0, x, y, n=46, spread=520, dur=2.2, seed=3):
    rnd = random.Random(seed)
    cols = (GREEN, GOLD, WARN, (60, 130, 200), (222, 120, 70))
    lt = t - t0
    if lt < 0 or lt > dur:
        return
    for i in range(n):
        ang = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = rnd.uniform(0.4, 1.0) * spread
        px = x + math.cos(ang) * sp * (1 - math.exp(-lt * 2.2)) * 1.0
        py = y + math.sin(ang) * sp * (1 - math.exp(-lt * 2.2)) + 380 * lt * lt * 0.5
        s = rnd.uniform(10, 20)
        rot = rnd.uniform(0, 6) + lt * rnd.uniform(-8, 8)
        col = cols[i % len(cols)]
        pts = [(px + math.cos(rot + k * math.pi / 2) * s, py + math.sin(rot + k * math.pi / 2) * s * 0.55) for k in range(4)]
        c.poly(pts, fill=col)


def sparkle(c, x, y, r, t, seed=0, color=GOLD):
    s = 0.6 + 0.4 * math.sin(t * 8 + seed)
    c.poly([(x, y - r * s), (x + r * 0.22 * s, y - r * 0.22 * s), (x + r * s, y), (x + r * 0.22 * s, y + r * 0.22 * s),
            (x, y + r * s), (x - r * 0.22 * s, y + r * 0.22 * s), (x - r * s, y), (x - r * 0.22 * s, y - r * 0.22 * s)], fill=color)


def iris_wipe(base, new, u, cx=W / 2, cy=H / 2):
    """Reveal `new` through a growing circle over `base` (both PIL images, same size)."""
    if u <= 0:
        return base
    if u >= 1:
        return new
    r = (math.hypot(W, H) * 0.62) * ease(u)
    mask = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    out = base.copy()
    out.paste(new, (0, 0), mask)
    return out


# ---------- rendering ----------
def render_video(frame_fn, duration, out_path, workers=6, audio=None, initializer=None, initargs=()):
    import multiprocessing as mp
    from imageio_ffmpeg import get_ffmpeg_exe

    n = int(duration * FPS)
    ff = get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", "-movflags", "+faststart",
            str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    with mp.Pool(workers, initializer=initializer, initargs=initargs) as pool:
        for im in pool.imap(frame_fn, range(n), chunksize=4):
            proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    return n


# ---------- simpler character styles (for comparison / future use) ----------
SHAPES = {
    #           head  torso legs  arms  torso-width  limb-width
    "slim":   dict(head=1.0, torso=1.0, legs=1.0, arms=1.0, tw=2.6, lw=24),
    "round":  dict(head=1.2, torso=0.85, legs=0.72, arms=0.8, tw=4.2, lw=22),
    "chibi":  dict(head=1.55, torso=0.62, legs=0.55, arms=0.7, tw=3.4, lw=20),
}


def draw_simple(c, x, y, pose, style="stick", scale=1.0, flip=False, t=0.0, color=INK, bg=WHITE, gaze=(1.0, 0.0),
                acc=None, acc_color=(244, 190, 60), shape="slim"):
    """Minimal people. style 'stick': black line figure, white round head.
    style 'bean': one solid colour for the whole body (head, torso, limbs), no hair or clothes.
    shape: 'slim', 'round', 'chibi' (bean proportions)."""
    p = dict(get_pose(pose))
    sh = SHAPES[shape] if style == "bean" else SHAPES["slim"]
    m = -1 if flip else 1
    k = scale
    breathe = math.sin(t * 2.4) * 1.4
    lw = (17 if style == "stick" else sh["lw"]) * k
    col = color
    T_, TH_, SH_, UA_, FA_ = TORSO * sh["torso"], TH * sh["legs"], SH * sh["legs"], UA * sh["arms"], FA * sh["arms"]

    def limb(origin, a1, a2, l1, l2):
        d1 = dirv(a1)
        j = (origin[0] + m * d1[0] * l1 * k, origin[1] + d1[1] * l1 * k)
        d2 = dirv(a1 + a2)
        return j, (j[0] + m * d2[0] * l2 * k, j[1] + d2[1] * l2 * k)

    hip = (x, y)
    lean = math.radians(p["lean"])
    top = (x + m * math.sin(lean) * T_ * k, y - math.cos(lean) * T_ * k + breathe * k)
    for a, b in (p["lb"], p["lf"]):
        j, e = limb(hip, a, b, TH_, SH_)
        c.line([hip, j, e], lw, col)
    hands = {}
    for key in ("ab", "af"):
        j, e = limb(top, *p[key], UA_, FA_)
        c.line([top, j, e], lw, col)
        hands[key] = e
    c.line([hip, top], lw * (1.0 if style == "stick" else sh["tw"]), col)
    tilt = math.radians(p["tilt"])
    r = HEADR * k * (1.0 if style == "stick" else 1.08 * sh["head"])
    neck = (NECK + HEADR * 0.6) * k
    hc = (top[0] + m * math.sin(tilt) * (neck + r), top[1] - math.cos(tilt) * (neck + r))
    if style == "stick":
        c.circle(hc[0], hc[1], r, fill=bg, outline=col, w=lw * 0.62)
        eye_col, white = col, False
    else:
        c.circle(hc[0], hc[1], r, fill=col)
        eye_col, white = INK, True
    blink = (t % 3.4) < 0.12
    for sx in (0.28, 0.78):
        ex, ey = hc[0] + m * r * sx, hc[1] - r * 0.05
        if blink:
            c.line([(ex - r * 0.12, ey), (ex + r * 0.12, ey)], 3 * k, eye_col if not white else WHITE)
        elif white:
            c.circle(ex, ey, r * 0.17, fill=WHITE)
            c.circle(ex + m * gaze[0] * r * 0.06, ey + gaze[1] * r * 0.06, r * 0.085, fill=INK)
        else:
            c.circle(ex, ey, r * 0.09, fill=eye_col)
    mx, my = hc[0] + m * r * 0.52, hc[1] + r * 0.46
    mc = WHITE if white else col
    mouth, mw = p["mouth"], max(3, 4 * k)
    if mouth == "smile":
        c.arc(mx, my - r * 0.16, r * 0.26, 25, 155, mw, mc)
    elif mouth == "grin":
        c.pie(mx, my - r * 0.05, r * 0.28, 0, 180, mc)
    elif mouth == "sad":
        c.arc(mx, my + r * 0.16, r * 0.24, 205, 335, mw, mc)
    elif mouth == "o":
        c.circle(mx, my, r * 0.11, fill=mc)
    else:
        c.line([(mx - r * 0.2, my), (mx + r * 0.2, my)], mw, mc)
    if acc:
        accessory(c, acc, hc, r, m, k, top, acc_color, color)
    return {"head": hc, "top": top, "hands": hands}


def draw_jelly(c, x, y, pose, scale=1.0, flip=False, t=0.0, color=INK, gaze=(1.0, 0.0)):
    """Jellybean person: head and body are one capsule; short arms and legs."""
    p = dict(get_pose(pose))
    m = -1 if flip else 1
    k = scale
    breathe = math.sin(t * 2.4) * 2.0
    lw = 24 * k
    body_h, body_w = 250 * k, 150 * k
    lean = math.radians(p["lean"] * 0.8)
    bottom = (x, y)
    topc = (x + m * math.sin(lean) * body_h, y - math.cos(lean) * body_h + breathe)

    def limb(origin, a1, a2, l1, l2):
        d1 = dirv(a1)
        j = (origin[0] + m * d1[0] * l1 * k, origin[1] + d1[1] * l1 * k)
        d2 = dirv(a1 + a2)
        return j, (j[0] + m * d2[0] * l2 * k, j[1] + d2[1] * l2 * k)

    for a, b in (p["lb"], p["lf"]):
        j, e = limb(bottom, a * 0.9, b * 0.9, 62, 52)
        c.line([bottom, j, e], lw, color)
    sh_pt = (lerp(bottom[0], topc[0], 0.62), lerp(bottom[1], topc[1], 0.62))
    c.line([bottom, topc], body_w, color)
    darker = tuple(int(v * 0.8) for v in color)
    for key in ("ab", "af"):
        j, e = limb((sh_pt[0] + m * body_w * 0.34, sh_pt[1]) if key == "af" else (sh_pt[0] - m * body_w * 0.34, sh_pt[1]), *p[key], 54, 48)
        c.line([(sh_pt[0] + (m if key == "af" else -m) * body_w * 0.34, sh_pt[1]), j, e], lw * 0.9, darker)
    fc = (lerp(bottom[0], topc[0], 0.78), lerp(bottom[1], topc[1], 0.78) - 4 * k)
    r = body_w / 2
    blink = (t % 3.4) < 0.12
    tilt = p["tilt"] / 40.0
    for sx in (0.12, 0.62):
        ex, ey = fc[0] + m * (r * sx + tilt * r * 0.25), fc[1] - r * 0.12
        if blink:
            c.line([(ex - r * 0.12, ey), (ex + r * 0.12, ey)], 3 * k, WHITE)
        else:
            c.circle(ex, ey, r * 0.2, fill=WHITE)
            c.circle(ex + m * gaze[0] * r * 0.07, ey + gaze[1] * r * 0.07, r * 0.1, fill=INK)
    mx, my = fc[0] + m * r * 0.4, fc[1] + r * 0.34
    mouth, mw = p["mouth"], max(3, 4 * k)
    if mouth == "smile":
        c.arc(mx, my - r * 0.15, r * 0.26, 25, 155, mw, WHITE)
    elif mouth == "grin":
        c.pie(mx, my - r * 0.05, r * 0.3, 0, 180, WHITE)
    elif mouth == "sad":
        c.arc(mx, my + r * 0.15, r * 0.24, 205, 335, mw, WHITE)
    elif mouth == "o":
        c.circle(mx, my, r * 0.12, fill=WHITE)
    else:
        c.line([(mx - r * 0.2, my), (mx + r * 0.2, my)], mw, WHITE)
    return {"head": fc, "top": topc}


def accessory(c, kind, hc, r, m, k, top, col, body):
    x, y = hc
    dark = tuple(int(v * 0.75) for v in col)
    if kind == "beanie":
        c.pie(x, y, r * 1.08, 192, 348, col)
        c.rrect(x - r * 1.04, y - r * 0.42, x + r * 1.04, y - r * 0.2, r * 0.1, fill=dark)
        c.circle(x, y - r * 1.12, r * 0.22, fill=WHITE)
    elif kind == "cap":
        c.pie(x, y, r * 1.08, 190, 350, col)
        c.line([(x + m * r * 0.35, y - r * 0.38), (x + m * r * 1.55, y - r * 0.3)], r * 0.2, dark)
    elif kind == "headphones":
        c.arc(x, y, r * 1.14, 195, 345, r * 0.16, INK)
        for sx in (-1, 1):
            c.rrect(x + sx * r * 1.12 - r * 0.2, y - r * 0.32, x + sx * r * 1.12 + r * 0.2, y + r * 0.32, r * 0.14, fill=col)
    elif kind == "glasses":
        for sx in (0.28, 0.78):
            c.circle(x + m * r * sx, y - r * 0.05, r * 0.27, outline=INK, w=3.2 * k)
        c.line([(x + m * r * 0.55, y - r * 0.05), (x + m * r * 0.51, y - r * 0.05)], 3 * k, INK)
        c.line([(x + m * r * 1.05, y - r * 0.05), (x + m * r * 1.0, y - r * 0.12)], 3 * k, INK, cap=False)
    elif kind == "sprout":
        c.line([(x, y - r * 0.95), (x + m * r * 0.05, y - r * 1.5)], r * 0.1, (90, 170, 100))
        for sx, rot in ((-1, -30), (1, 30)):
            lx, ly = x + sx * r * 0.32, y - r * 1.55
            c.poly([(x, y - r * 1.4), (lx - sx * r * 0.05, ly - r * 0.22), (lx + sx * r * 0.28, ly + r * 0.05)], fill=(120, 200, 120))
    elif kind == "scarf":
        bx = top[0]
        c.line([(bx - r * 0.78, top[1] - r * 0.12), (bx + r * 0.78, top[1] - r * 0.12)], r * 0.36, col)
        c.rrect(bx - m * r * 0.78 - r * 0.2, top[1] - r * 0.12, bx - m * r * 0.78 + r * 0.2, top[1] + r * 0.95, r * 0.1, fill=dark)
    elif kind == "tophat":
        c.rrect(x - r * 0.95, y - r * 0.95, x + r * 0.95, y - r * 0.78, r * 0.06, fill=INK)
        c.rrect(x - r * 0.55, y - r * 1.65, x + r * 0.55, y - r * 0.85, r * 0.08, fill=INK)
        c.rrect(x - r * 0.55, y - r * 1.05, x + r * 0.55, y - r * 0.9, 0, fill=col)
