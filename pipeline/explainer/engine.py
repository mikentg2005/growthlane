"""Tiny 2D explainer-video engine: stick-figure characters, props, text and a timeline.

Renders 1080x1920 frames with Pillow (drawn at 2x and reduced for smooth edges) and
pipes them to ffmpeg (bundled by the imageio-ffmpeg package). No external assets,
no paid tools. A video is a function frame(i) -> PIL image; scenes are plain
Python functions that draw one moment in time.

Setup once:  python -m pip install --user imageio-ffmpeg
"""
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SS = 1080, 1920, 30, 2
PAPER, INK, MUTED, GREEN = (247, 245, 238), (23, 32, 27), (86, 99, 91), (29, 95, 74)
WARN, WARN_SOFT, GREEN_SOFT, LINE = (154, 74, 43), (243, 228, 220), (227, 238, 232), (218, 214, 200)
GOLD = (196, 150, 40)

FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    path = {"head": "GeorgiaPro-Bold.ttf", "bold": "arialbd.ttf", "text": "arial.ttf"}[name]
    return ImageFont.truetype(str(FONTS / path), int(size * SS))


# ---------- math helpers ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def mix(c1, c2, u):
    u = clamp(u)
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def prog(t, t0, dur):
    """0..1 eased progress of an event that starts at t0 and lasts dur seconds."""
    return ease((t - t0) / dur)


# ---------- low-level drawing (all coordinates in 1080x1920 space) ----------
class Canvas:
    def __init__(self):
        self.img = Image.new("RGB", (W * SS, H * SS), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def line(self, pts, w, color):
        pts = [(x * SS, y * SS) for x, y in pts]
        self.d.line(pts, fill=color, width=int(w * SS), joint="curve")
        r = w * SS / 2
        for x, y in {pts[0], pts[-1]} | set(pts[1:-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def circle(self, cx, cy, r, fill=None, outline=None, w=0):
        self.d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS],
                       fill=fill, outline=outline, width=int(w * SS))

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, w=0):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS,
                                 fill=fill, outline=outline, width=int(w * SS))

    def poly(self, pts, fill=None):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)

    def arc(self, cx, cy, r, a0, a1, w, color):
        self.d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], a0, a1,
                   fill=color, width=int(w * SS))

    def text(self, s, x, y, f, color=INK, anchor="la"):
        self.d.text((x * SS, y * SS), s, font=f, fill=color, anchor=anchor)

    def tw(self, s, f):
        return self.d.textlength(s, font=f) / SS

    def wrap(self, s, f, width):
        lines, cur = [], ""
        for w in s.split():
            t = (cur + " " + w).strip()
            if self.tw(t, f) <= width:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def reveal(self, s, x, y, f, width, t, t0, color=INK, lh=1.3, align="center", per=0.09):
        """Draw wrapped text whose words fade in one after another starting at t0."""
        fs = f.size / SS
        n = 0
        for line in self.wrap(s, f, width):
            words = line.split()
            total = self.tw(line, f)
            cx = x - total / 2 if align == "center" else x
            space = self.tw(" ", f)
            for w in words:
                a = clamp((t - t0 - n * per) / 0.25)
                if a > 0:
                    self.text(w, cx, y + (1 - ease(a)) * 14, f, mix(PAPER, color, a), "la")
                cx += self.tw(w, f) + space
                n += 1
            y += fs * lh
        return n * per + 0.25

    def frame(self):
        return self.img.reduce(SS)


# ---------- the stick figure ----------
# Angles are degrees from "straight down": 0 = down, +90 = toward the front, 180 = straight up.
# For each limb the pair is (shoulder-or-hip angle, elbow-or-knee angle relative to it).
POSES = {
    "stand":   dict(lean=0, tilt=0, af=(14, 8), ab=(-14, -8), lf=(6, 0), lb=(-6, 0), face="flat"),
    "slump":   dict(lean=14, tilt=18, af=(8, 4), ab=(-4, -2), lf=(10, 0), lb=(-4, 0), face="sad"),
    "shrug":   dict(lean=0, tilt=8, af=(62, 70), ab=(-62, -70), lf=(6, 0), lb=(-6, 0), face="flat"),
    "worry":   dict(lean=4, tilt=10, af=(150, -118), ab=(-8, -4), lf=(6, 0), lb=(-6, 0), face="worry"),
    "reach":   dict(lean=6, tilt=-4, af=(98, 4), ab=(-24, -10), lf=(10, 0), lb=(-10, 0), face="smile"),
    "cheer":   dict(lean=-2, tilt=-6, af=(128, 40), ab=(-128, -40), lf=(10, 0), lb=(-10, 0), face="smile"),
    "sit":     dict(lean=0, tilt=0, af=(52, 42), ab=(40, 36), lf=(92, -92), lb=(86, -88), face="flat"),
    "sitlook": dict(lean=-4, tilt=-22, af=(52, 42), ab=(40, 36), lf=(92, -92), lb=(86, -88), face="worry"),
    "walkA":   dict(lean=4, tilt=0, af=(40, 20), ab=(-40, -20), lf=(34, -14), lb=(-30, -6), face="smile"),
    "walkB":   dict(lean=4, tilt=0, af=(-40, -20), ab=(40, 20), lf=(-30, -6), lb=(34, -14), face="smile"),
}
TORSO, NECK, HEADR, UA, FA, TH, SH = 150, 20, 46, 66, 62, 86, 84


def pose_mix(a, b, u):
    a, b = get_pose(a), get_pose(b)
    out = {}
    for k in a:
        if k == "face":
            out[k] = a[k] if u < 0.5 else b[k]
        elif isinstance(a[k], tuple):
            out[k] = tuple(lerp(x, y, u) for x, y in zip(a[k], b[k]))
        else:
            out[k] = lerp(a[k], b[k], u)
    return out


def get_pose(p):
    return POSES[p] if isinstance(p, str) else p


def dirv(deg):
    r = math.radians(deg)
    return math.sin(r), math.cos(r)


def draw_figure(c, x, y, pose, scale=1.0, flip=False, color=INK, shirt=GREEN):
    """Draw a figure whose hip is at (x, y). Returns key points."""
    p = get_pose(pose)
    m = -1 if flip else 1
    k = scale

    def limb(origin, a1, a2, l1, l2):
        d1 = dirv(a1)
        j = (origin[0] + m * d1[0] * l1 * k, origin[1] + d1[1] * l1 * k)
        d2 = dirv(a1 + a2)
        e = (j[0] + m * d2[0] * l2 * k, j[1] + d2[1] * l2 * k)
        return j, e

    hip = (x, y)
    lean = math.radians(p["lean"])
    top = (x + m * math.sin(lean) * TORSO * k, y - math.cos(lean) * TORSO * k)
    w = 15 * k
    for a, b in (p["lb"], p["lf"]):
        j, e = limb(hip, a, b, TH, SH)
        c.line([hip, j, e], w, color)
        c.line([e, (e[0] + m * 22 * k, e[1])], w, color)
    j, e = limb(top, *p["ab"], UA, FA)
    c.line([top, j, e], w, color)
    c.line([hip, top], w + 9 * k, shirt)
    tilt = math.radians(p["tilt"])
    hc = (top[0] + m * math.sin(tilt) * (NECK + HEADR) * k, top[1] - math.cos(tilt) * (NECK + HEADR) * k)
    c.line([top, hc], w, color)
    c.circle(hc[0], hc[1], HEADR * k, fill=PAPER, outline=color, w=w * 0.8)
    face(c, hc, HEADR * k, p["face"], m, color)
    j, e = limb(top, *p["af"], UA, FA)
    c.line([top, j, e], w, color)
    return {"head": hc, "hand": e, "top": top}


def face(c, hc, r, kind, m, color):
    ex = r * 0.34
    ey = -r * 0.12
    for sx in (-1, 1):
        c.circle(hc[0] + m * (sx * ex + r * 0.18), hc[1] + ey, max(2.5, r * 0.07), fill=color)
    mx, my = hc[0] + m * r * 0.18, hc[1] + r * 0.38
    lw = max(3, r * 0.08)
    if kind == "smile":
        c.arc(mx, my - r * 0.22, r * 0.34, 20, 160, lw, color)
    elif kind == "sad":
        c.arc(mx, my + r * 0.2, r * 0.3, 200, 340, lw, color)
    elif kind == "worry":
        c.circle(mx, my, r * 0.11, outline=color, w=lw)
    else:
        c.line([(mx - r * 0.2, my), (mx + r * 0.2, my)], lw, color)


# ---------- props ----------
def meter(c, x, y, level, label="MOTIVATION", h=420, w=64):
    c.text(label, x, y - 46, font("bold", 26), MUTED, "mm")
    c.rrect(x - w / 2, y, x + w / 2, y + h, 22, fill=(236, 232, 220), outline=LINE, w=3)
    lv = clamp(level)
    col = mix(WARN, GREEN, ease((lv - 0.2) / 0.5))
    fh = max(w - 12, (h - 12) * lv)
    c.rrect(x - w / 2 + 6, y + h - 6 - fh, x + w / 2 - 6, y + h - 6, 16, fill=col)


def phone(c, x, y, shake=0.0):
    dx = math.sin(shake * 60) * 6 if shake else 0
    c.rrect(x - 40 + dx, y - 70, x + 40 + dx, y + 70, 14, fill=INK)
    c.rrect(x - 32 + dx, y - 58, x + 32 + dx, y + 56, 8, fill=(200, 215, 208))


def bubble(c, x, y, w, h, tail_to=None):
    c.rrect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, 36, fill=(255, 253, 248), outline=INK, w=5)
    if tail_to:
        tx, ty = tail_to
        for i, rr in enumerate((16, 11, 7)):
            u = 0.3 + i * 0.28
            c.circle(lerp(x, tx, u), lerp(y + h / 2, ty, u), rr, fill=(255, 253, 248), outline=INK, w=4)


def pill(c, x, y, label, color=GREEN, size=30):
    f = font("bold", size)
    wd = c.tw(label, f) + 56
    c.rrect(x - wd / 2, y - 34, x + wd / 2, y + 34, 34, fill=color)
    c.text(label, x, y, f, (255, 255, 255), "mm")


def diamond(c, cx, cy, r, color=GREEN, stroke=6):
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
    c.line(pts, stroke, color)
    ri = r * 0.38
    c.poly([(cx, cy - ri), (cx + ri, cy), (cx, cy + ri), (cx - ri, cy)], fill=color)


def flag(c, x, ground_y, h, label=None, color=WARN):
    c.line([(x, ground_y), (x, ground_y - h)], max(4, h * 0.05), INK)
    c.poly([(x, ground_y - h), (x + h * 0.5, ground_y - h * 0.8), (x, ground_y - h * 0.6)], fill=color)
    if label:
        c.text(label, x, ground_y + 40, font("bold", 28), color, "mm")


def mountain(c, x, ground_y, w, h, color=(207, 202, 186)):
    c.poly([(x - w / 2, ground_y), (x, ground_y - h), (x + w / 2, ground_y)], fill=color)
    sw = w * 0.12
    c.poly([(x - sw, ground_y - h + sw * 2 * h / w), (x, ground_y - h), (x + sw, ground_y - h + sw * 2 * h / w)],
           fill=(250, 248, 242))


def ground(c, y, x0=60, x1=1020):
    c.line([(x0, y), (x1, y)], 6, INK)


def footer(c):
    diamond(c, 78, H - 90, 18, GREEN, 3)
    c.text("GrowthLane", 110, H - 112, font("head", 34), INK)


# ---------- rendering ----------
def render_video(frame_fn, duration, out_path, workers=6):
    import multiprocessing as mp
    from imageio_ffmpeg import get_ffmpeg_exe

    n = int(duration * FPS)
    cmd = [get_ffmpeg_exe(), "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
           "-movflags", "+faststart", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    with mp.Pool(workers) as pool:
        for im in pool.imap(frame_fn, range(n), chunksize=4):
            proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    return n
