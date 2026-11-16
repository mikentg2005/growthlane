"""Paper-notebook look for the explainer machine: lined page, hand-drawn doodles that draw on,
handwritten text that writes on, page flip transition, and the Alex bean character.

All coordinates are in the 1080x1920 page. Doodles are lists of strokes; a stroke is
(points, width). Drawing a doodle with progress p reveals the strokes in order, like a pen.
"""
import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from engine2 import (  # noqa: F401
    Canvas, FPS, GREEN, H, MUTED, SS, W, _font, clamp, draw_simple, ease, gradient, lerp, mix, out_back,
    out_cubic, out_elastic, prog,
)

INK = (36, 54, 112)          # blue ballpoint
INK_DARK = (28, 36, 64)
RED = (196, 62, 52)          # red pen for emphasis
GREEN_PEN = (34, 120, 84)
PAPER_TOP, PAPER_BOTTOM = (251, 247, 234), (242, 236, 216)
LINE_BLUE = (198, 212, 228)
MARGIN_RED = (230, 160, 160)
ALEX = (29, 95, 74)          # Alex's green
MATE = (96, 104, 122)        # neutral slate grey, for a second character


# ---------- page ----------
@lru_cache(maxsize=1)
def paper_bg():
    c = Canvas(gradient(PAPER_TOP, PAPER_BOTTOM))
    for y in range(250, H, 64):
        c.line([(0, y), (W, y)], 2, LINE_BLUE, cap=False)
    c.line([(104, 0), (104, H)], 3, MARGIN_RED, cap=False)
    for rx in range(70, W, 105):  # spiral binding along the top edge
        c.circle(rx, 8, 17, outline=(120, 120, 126), w=5)
    return c.img


def new_page():
    return Canvas(paper_bg())


# ---------- strokes ----------
def circ(cx, cy, r, n=30, a0=0, a1=360):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def wobble(pts, amp=2.2, seed=1):
    rnd = random.Random(seed)
    out = []
    for i, (x, y) in enumerate(pts):
        out.append((x + math.sin(i * 1.7 + seed) * amp + rnd.uniform(-amp, amp) * 0.4,
                    y + math.cos(i * 1.3 + seed) * amp + rnd.uniform(-amp, amp) * 0.4))
    return out


def seg_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def draw_strokes(c, strokes, p, ox, oy, s=1.0, color=INK, width=7):
    """Draw strokes (local coords) at (ox, oy) scaled by s, revealed up to progress p (0..1)."""
    p = clamp(p)
    if p <= 0:
        return
    lens = [seg_len(pts) for pts, _w in strokes]
    total = sum(lens) or 1
    target = total * p
    done = 0.0
    for (pts, w), ln in zip(strokes, lens):
        if done >= target:
            break
        take = min(ln, target - done)
        done += ln
        if ln == 0:
            continue
        part = [pts[0]]
        acc = 0.0
        for i in range(len(pts) - 1):
            d = math.dist(pts[i], pts[i + 1])
            if acc + d >= take:
                f = (take - acc) / d if d else 0
                part.append((lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)))
                break
            part.append(pts[i + 1])
            acc += d
        pts2 = [(ox + x * s, oy + y * s) for x, y in part]
        if len(pts2) >= 2:
            c.line(pts2, (w if w else width) * max(0.6, s ** 0.5), color)


# ---------- doodle library (local coords, about +/-110) ----------
def D_lightbulb():
    st = [(wobble(circ(0, -20, 58, 28, 130, 410), 1.5, 1), 7)]
    st += [([(-26, 40), (-22, 62), (22, 62), (26, 40)], 7), ([(-18, 80), (18, 80)], 7)]
    for a in (-70, -35, 0, 35, 70):
        r = math.radians(a - 90)
        st.append(([(math.cos(r) * 82, -20 + math.sin(r) * 82), (math.cos(r) * 108, -20 + math.sin(r) * 108)], 6))
    return st


def D_calendar(circle_day=True):
    st = [(wobble(rect(-90, -85, 90, 90), 1.4, 2), 7), ([(-90, -40), (90, -40)], 7),
          ([(-45, -100), (-45, -70)], 8), ([(45, -100), (45, -70)], 8)]
    for r in range(3):
        for q in range(5):
            x, y = -62 + q * 31, -10 + r * 32
            st.append(([(x - 4, y), (x + 4, y)], 5))
    return st


def D_circle_day():
    return [(wobble(circ(32, 55, 25, 26), 1.5, 3), 6)]


def D_clock():
    return [(wobble(circ(0, 0, 80, 34), 1.4, 4), 7), ([(0, 0), (0, -50)], 7), ([(0, 0), (36, 22)], 7),
            ([(0, -78), (0, -66)], 5), ([(78, 0), (66, 0)], 5), ([(0, 78), (0, 66)], 5), ([(-78, 0), (-66, 0)], 5)]


def D_phone(buzz=True):
    st = [(wobble(rect(-45, -80, 45, 80), 1.2, 5), 7), ([(-36, -64), (36, -64), (36, 54), (-36, 54), (-36, -64)], 5),
          (circ(0, 67, 6, 12), 5)]
    if buzz:
        for sx in (-1, 1):
            for k in (1, 2):
                st.append(([(sx * (58 + k * 16), -26), (sx * (68 + k * 16), 0), (sx * (58 + k * 16), 26)], 5))
    return st


def D_laptop():
    return [(wobble(rect(-100, -75, 100, 40), 1.4, 6), 7), ([(-125, 52), (125, 52), (108, 70), (-108, 70), (-125, 52)], 7),
            ([(-80, -50), (-20, -50)], 5), ([(-80, -30), (30, -30)], 5)]


def D_desk(w=420):
    return [([(-w / 2, 0), (w / 2, 0)], 8), ([(-w / 2 + 30, 0), (-w / 2 + 30, 190)], 8), ([(w / 2 - 30, 0), (w / 2 - 30, 190)], 8)]


def D_chair():
    return [([(-70, 0), (30, 0)], 8), ([(-70, 0), (-70, -150)], 8), ([(-40, 0), (-40, 82)], 8), ([(-70, 82), (0, 82)], 8)]


def D_check():
    return [(wobble([(-44, 2), (-12, 34), (50, -38)], 1.2, 7), 11)]


def D_heart():
    pts = [(16 * math.sin(t) ** 3 * 4.6, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * 4.6)
           for t in [i * 2 * math.pi / 40 for i in range(41)]]
    return [(wobble(pts, 1.2, 8), 7)]


def D_bolt():
    return [([(10, -90), (-52, 12), (-6, 12), (-20, 90), (52, -20), (4, -20), (10, -90)], 7)]


def D_hourglass():
    return [([(-50, -85), (50, -85)], 8), ([(-50, 85), (50, 85)], 8),
            ([(-42, -85), (-42, -60), (0, 0), (-42, 60), (-42, 85)], 7), ([(42, -85), (42, -60), (0, 0), (42, 60), (42, 85)], 7),
            ([(-22, 70), (22, 70), (0, 50), (-22, 70)], 5)]


def D_question():
    pts = circ(0, -40, 52, 26, 200, 450) + [(0, 20), (0, 38)]
    return [(wobble(pts, 1.5, 9), 12), (circ(0, 78, 7, 10), 12)]


def D_arrow(x0, y0, x1, y1):
    ang = math.atan2(y1 - y0, x1 - x0)
    h = 22
    return [([(x0, y0), (x1, y1)], 7),
            ([(x1 - h * math.cos(ang - 0.5), y1 - h * math.sin(ang - 0.5)), (x1, y1),
              (x1 - h * math.cos(ang + 0.5), y1 - h * math.sin(ang + 0.5))], 7)]


def D_underline(w, wavy=True):
    pts = [(-w / 2 + i * w / 20, math.sin(i * 0.9) * 5 if wavy else 0) for i in range(21)]
    return [(pts, 7)]


def D_cross(w=120, h=26):
    return [([(-w / 2, -h), (w / 2, h)], 8), ([(-w / 2, h), (w / 2, -h)], 8)]


def D_up_arrow():
    return [([(0, 50), (0, -50)], 8), ([(-26, -22), (0, -52), (26, -22)], 8)]


def D_down_arrow():
    return [([(0, -50), (0, 50)], 8), ([(-26, 22), (0, 52), (26, 22)], 8)]


def D_bar():
    return [([(-280, 0), (280, 0)], 8)]


def D_ground():
    return [([(-430, 0), (430, 0)], 6)]


def D_chair_desk():
    return D_chair()


def D_receipt():
    zig = []
    for i in range(9):
        x = -50 + i * 12.5
        zig.append((x, 95 if i % 2 == 0 else 80))
    pts = [(-50, -95), (50, -95), (50, 80)] + zig + [(-50, -95)]
    st = [(wobble(pts, 1.0, 10), 6)]
    for i, y in enumerate((-60, -30, 0, 30)):
        st.append(([(-30, y), (30 if i != 3 else 10, y)], 4))
    return st


def D_candy():
    st = [(wobble(circ(0, 0, 44, 22), 1.3, 11), 7)]
    for sx in (-1, 1):
        st.append(([(sx * 44, -22), (sx * 78, -36), (sx * 70, 0), (sx * 78, 36), (sx * 44, 22)], 6))
    return st


# ---------- handwriting ----------
def write(c, s, x, y, size, color=INK, p=1.0, anchor="mm", font="hand"):
    """Handwritten text that writes on from left to right (p = 0..1)."""
    p = clamp(p)
    if p <= 0 or not s:
        return
    f = _font(font, size * SS)
    l, t, r, b = f.getbbox(s)
    w, h = r - l + 12, b - t + 12
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((-l + 6, -t + 6), s, font=f, fill=color + (255,))
    cut = max(1, int(w * ease(p) ** 0.9))
    tmp = tmp.crop((0, 0, cut, h))
    px = x * SS - (w / 2 if anchor[0] == "m" else 0)
    py = y * SS - h / 2
    c.img.paste(tmp, (int(px), int(py)), tmp)


def text_width(s, size, font="hand"):
    f = _font(font, size * SS)
    l, t, r, b = f.getbbox(s)
    return (r - l) / SS


def bubble(c, x, y, text, size, tail_to=None, p=1.0, color=INK):
    """Hand-drawn speech/thought bubble that pops in."""
    if p <= 0:
        return
    k = out_back(clamp(p))
    w = text_width(text, size) + 70
    h = size * 1.5 + 36
    x0, x1, y0, y1 = x - w / 2 * k, x + w / 2 * k, y - h / 2 * k, y + h / 2 * k
    c.rrect(x0, y0, x1, y1, 38 * k, fill=(255, 253, 246), outline=color, w=5)
    if tail_to:
        tx, ty = tail_to
        for i, rr in enumerate((16, 11, 7)):
            u = 0.3 + i * 0.28
            c.circle(lerp(x, tx, u), lerp(y + h / 2, ty, u), rr * k, fill=(255, 253, 246), outline=color, w=4)
    if k > 0.8:
        write(c, text, x, y - 2, size, color, 1.0)


# ---------- page flip ----------
def flip_page(old, new, u):
    """Top-bound notebook: the old page flips up and away, revealing the new one."""
    u = clamp(u)
    if u <= 0:
        return old
    if u >= 1:
        return new
    out = new.copy()
    th = u * math.pi / 2          # 0..90 degrees
    hh = max(2, int(H * math.cos(th)))
    page = old.resize((W, hh), Image.BILINEAR)
    shade = Image.new("RGB", (W, hh), (0, 0, 0))
    page = Image.blend(page, shade, 0.22 * u)
    # shadow on the new page under the flipping edge
    sh = Image.new("L", (W, 60), 0)
    d = ImageDraw.Draw(sh)
    for i in range(60):
        d.line([(0, i), (W, i)], fill=int(90 * (1 - i / 60) * (1 - u * 0.5)))
    black = Image.new("RGB", (W, 60), (0, 0, 0))
    out.paste(black, (0, hh), sh)
    out.paste(page, (0, 0))
    d2 = ImageDraw.Draw(out)
    for rx in range(70, W, 105):  # spiral rings at the top edge
        d2.ellipse([rx - 11, -6, rx + 11, 28], outline=(120, 120, 126), width=5)
    return out


# ---------- Alex ----------
def alex(c, x, y, pose, t=0.0, flip=False, gaze=(1.0, 0.0), scale=1.0):
    return draw_simple(c, x, y, pose, "stick", scale, flip=flip, t=t, color=ALEX, bg=PAPER_TOP, gaze=gaze)


def mate(c, x, y, pose, t=0.0, flip=False, gaze=(1.0, 0.0), scale=1.0):
    """A second, neutral-grey stick-figure character (a colleague)."""
    return draw_simple(c, x, y, pose, "stick", scale, flip=flip, t=t, color=MATE, bg=PAPER_TOP, gaze=gaze)
