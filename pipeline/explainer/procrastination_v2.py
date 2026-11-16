"""Explainer video v2: "The Procrastination Equation" (about 49 s, 1080x1920, music + sound effects).

Run from the repo root:
    python pipeline/explainer/procrastination_v2.py                 # full video with sound
    python pipeline/explainer/procrastination_v2.py --still 9.5     # one frame, for checking
    python pipeline/explainer/procrastination_v2.py --sheet         # contact sheet of key moments

Content comes from the sources in _posts/2026-11-13-best-books-on-procrastination.md
(Steel's formula as summarised in public outlines; Publishers Weekly; Straight.com review).
Alex and Sam are fictional characters. The final tip is labelled as ours.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine2 import *  # noqa: E402,F403

GROUND = 1270
SCENES = [("hook", 0.0), ("formula", 5.2), ("expect", 13.0), ("value", 19.6), ("impulse", 25.8),
          ("delay", 32.0), ("tip", 38.4), ("end", 44.8)]
TOTAL = 49.5
TRANS = 0.6
CAP_Y = 1400


def scene_at(t):
    idx = 0
    for i, (_, t0) in enumerate(SCENES):
        if t >= t0:
            idx = i
    return idx


# ---------- shared pieces ----------
def hud_title(c, t, t0, label, title, color=GREEN, size=68):
    a = prog(t, t0, 0.45, out_back)
    if label:
        pill(c, W / 2, 205 + (1 - clamp(a)) * 30, label, color, a=clamp(a))
    c.words(title, W / 2, 290, "head", size, 920, t, t0 + 0.15, INK, lh=1.12, per=0.06)


def hud_caption(c, t, t0, text, size=46, color=(64, 76, 69), hi=None, y=CAP_Y):
    a = prog(t, t0 - 0.2, 0.45, out_cubic)
    if a > 0 and text:
        with c.hud():
            n = len(c.wrap(text, "text", size, 900))
            h = n * size * 1.36 + 74
            top = y - 52 + (1 - a) * 70
            c.rrect(56, top + 8, W - 56, top + h + 8, 34, fill=(0, 0, 0, 0) if False else (220, 200, 182))
            c.rrect(56, top, W - 56, top + h, 34, fill=(255, 253, 248), outline=LINE, w=3)
    c.words(text, W / 2, y, "text", size, 900, t, t0, color, lh=1.36, per=0.065, hi=hi)


def hud_footer(c):
    with c.hud():
        pts = [(78, H - 108), (96, H - 90), (78, H - 72), (60, H - 90), (78, H - 108)]
        c.line(pts, 3, GREEN)
        c.poly([(78, H - 98), (86, H - 90), (78, H - 82), (70, H - 90)], fill=GREEN)
        c.text("GrowthLane", 112, H - 90, "head", 32, INK, "lm")
        c.rrect(0, 0, W, 14, 0, fill=GREEN)


def room_scene(c, t, cam, fast_clock=False, calendar_day=28, cal_stamp=None):
    c.cam(*cam)
    room(c, t, window=False)
    win(c, 70, 560, 300, 330, t)
    wall_calendar(c, 470, 520, 230, 230, "NOVEMBER", circled=calendar_day if cal_stamp is None else cal_stamp)
    wall_clock(c, 830, 610, 68, t, fast=fast_clock)
    plant(c, 90, GROUND, t)
    desk(c, 470, 990, 1030)
    lamp(c, 940, 1030)


def alex_seated(c, t, pose, gaze=(1, 0), scale=1.3, x=330, eyes="normal"):
    seat = GROUND - SH * scale
    chair(c, x, seat)
    return draw_person(c, x, seat, pose, ALEX, scale, t=t, gaze=gaze, shadow=(160, 120, 90), eyes=eyes)


# ---------- scenes (t = global time) ----------
def s_hook(c, t):
    t0 = 0.0
    k = ease(t / 5.2)
    room_scene(c, t, (lerp(540, 470, k), lerp(960, 990, k), lerp(1.0, 1.32, k)), fast_clock=True)
    laptop(c, 680, 1030, "blank", t=t)
    shake = (t - 3.0) if 3.0 < t < 4.8 else 0
    phone(c, 890, 1030 - 64, shake=shake, scale=0.8)
    pose = pose_mix("sit", "sitlook", prog(t, 2.9, 0.5))
    look = (1, 0.1) if t < 2.9 else (1.0, 0.6)
    f = alex_seated(c, t, pose, gaze=look)
    a = prog(t, 3.5, 0.7, out_elastic)
    if a > 0.02:
        speech(c, 560, 650 + math.sin(t * 3) * 5, 440 * a, 130 * a, "later…", 54, tail=(f["head"][0] + 40, f["head"][1] - 70),
               thought=True, a=clamp(a))
    hud_title(c, t, 0.2, None, "Why do we put things off?")
    hud_caption(c, t, 2.2, "It is usually blamed on laziness. Researchers see it differently.",
                hi={"laziness": WARN, "differently": GREEN})


def s_formula(c, t):
    t0 = SCENES[1][1]
    lt = t - t0
    c.img.paste(gradient((226, 240, 233), (200, 224, 214)), (0, 0))
    c.d = ImageDraw.Draw(c.img)
    c.cam()
    hud_title(c, t, t0 + 0.1, "THE FORMULA", "One research-based equation")
    # board
    a = prog(lt, 0.3, 0.6, out_cubic)
    y0 = 520 + (1 - a) * 120
    with c.hud():
        c.rrect(66, y0 + 14, W - 54, y0 + 770 + 14, 44, fill=(180, 204, 194))
        c.rrect(60, y0, W - 60, y0 + 770, 44, fill=(255, 253, 248))
        c.text("MOTIVATION  =", W / 2, y0 + 90, "head", 76, mix(PAPER, INK, clamp(a * 2 - 0.5)))
    rows = [(y0 + 270, GREEN, GREEN_SOFT, [("Expectancy", icon_check), ("Value", icon_heart)], (1.2, 1.7)),
            (y0 + 560, WARN, WARN_SOFT, [("Impulsiveness", icon_bolt), ("Delay", icon_hourglass)], (3.2, 3.7))]
    with c.hud():
        for ry, col, soft, items, whens in rows:
            for i, ((label, icon), when) in enumerate(zip(items, whens)):
                x = 300 if i == 0 else 780
                p = prog(lt, when, 0.5, out_back)
                if p > 0:
                    w2, h2 = 400 * p, 132 * p
                    c.rrect(x - w2 / 2, ry - h2 / 2, x + w2 / 2, ry + h2 / 2, 30 * p, fill=soft, outline=col, w=4)
                    if p > 0.8:
                        icon(c, x - 135, ry, 34, col)
                        c.text(label, x + 28, ry, "bold", 38, col)
            q = prog(lt, whens[0] + 0.25, 0.4, out_back)
            if q > 0:
                c.text("×", W / 2, ry, "head", 72 * q, MUTED)
        bar = prog(lt, 2.4, 0.6, out_cubic)
        c.line([(150, y0 + 415), (150 + 780 * bar, y0 + 415)], 8, INK)
        for ry, col, soft, items, whens in rows:
            pass
        u = prog(lt, 4.3, 0.5, out_back)
        if u > 0:
            c.rrect(W / 2 - 250 * u, y0 + 660 - 2, W / 2 + 250 * u, y0 + 740, 36 * u, fill=WARN) if False else None
    pill(c, W / 2, y0 + 372, "these push it UP", GREEN, 26, a=prog(lt, 2.0, 0.4)) if lt > 2.0 else None
    pill(c, W / 2, y0 + 678, "these pull it DOWN", WARN, 26, a=prog(lt, 4.3, 0.4)) if lt > 4.3 else None
    hud_caption(c, t, t0 + 0.9, "Researcher Piers Steel sums up the science of procrastination in one equation.",
                hi={"Piers": GREEN, "Steel": GREEN, "equation.": GREEN})


def s_expect(c, t):
    t0 = SCENES[2][1]
    lt = t - t0
    follow = prog(lt, 2.8, 2.6)
    c.cam(lerp(600, 760, follow), lerp(1060, 1010, follow), lerp(1.1, 1.0, follow))
    room(c, t, window=False)
    win(c, 70, 560, 300, 330, t)
    plant(c, 90, GROUND, t)
    split = prog(lt, 2.0, 0.9, out_cubic)
    steps = [(580, 120), (700, 240), (820, 360)]
    stair_col = [(206, 196, 178), (194, 184, 166), (182, 172, 154)]
    if split < 1:
        # the big scary stack, then it breaks into three steps
        hh = lerp(760, 120, split)
        bx0, bx1 = lerp(620, 580, split), lerp(840, 700, split)
        c.rrect(bx0, GROUND - hh, bx1, GROUND, 14, fill=(206, 196, 178), outline=(160, 150, 134), w=4)
        for i in range(1, 8):
            yy = GROUND - hh * i / 8
            c.line([(bx0 + 10, yy), (bx1 - 10, yy)], 3, (180, 170, 154), cap=False)
        if split < 0.05:
            c.text("BIG REPORT", (bx0 + bx1) / 2, GROUND - hh + 70, "bold", 30, MUTED)
            c.line([(bx0 + 36, GROUND - hh + 130), (bx0 + 70, GROUND - hh + 144)], 6, WARN)
            c.line([(bx1 - 36, GROUND - hh + 130), (bx1 - 70, GROUND - hh + 144)], 6, WARN)
    if split > 0:
        for i, ((x, h), col) in enumerate(zip(steps, stair_col)):
            sh = h * split
            c.rrect(x, GROUND - sh, x + 120, GROUND, 8, fill=col, outline=(150, 140, 124), w=3)
            if split > 0.9:
                c.text(f"step {i + 1}", x + 60, GROUND - sh + 34, "bold", 26, MUTED)
    # Alex: scared -> reaches -> hops up the steps
    hop = prog(lt, 3.0, 2.2, ease)
    path = [(300, 0), (470, 0), (640, 120), (760, 240), (880, 360)]
    seg = hop * (len(path) - 1)
    i0 = min(int(seg), len(path) - 2)
    u = seg - i0
    ax = lerp(path[i0][0], path[i0 + 1][0], u)
    ay = lerp(path[i0][1], path[i0 + 1][1], u) - math.sin(u * math.pi) * 40
    if lt < 2.0:
        pose, look = pose_mix("stand", "scared", prog(lt, 0.5, 0.4)), (0.4, -0.8)
    elif lt < 3.0:
        pose, look = pose_mix("scared", "reach", prog(lt, 2.2, 0.6)), (1, -0.3)
    elif hop < 1:
        pose, look = pose_mix("walkA", "walkB", (math.sin(lt * 9) + 1) / 2), (1, -0.1)
    else:
        pose, look = "cheer", (1, 0)
    scale = 1.25
    draw_person(c, ax, GROUND - 207 * scale / 1.25 - ay, pose, ALEX, scale, t=t, gaze=look, shadow=None)
    for i, (x, h) in enumerate(steps):
        if hop > (i + 1.4) / 4.5:
            pp = prog(lt, 3.0 + (i + 1.4) / 4.5 * 2.2, 0.35, out_back)
            icon_check(c, x + 60, GROUND - h - 70, 34 * pp, GREEN)
    confetti(c, t, t0 + 5.2, 900, GROUND - 400, seed=5) if lt > 5.2 else None
    hud_title(c, t, t0 + 0.1, "1  EXPECTANCY", "Can I actually do this?")
    meter(c, 975, 800, lerp(0.2, 0.86, prog(lt, 2.4, 2.8)))
    hud_caption(c, t, t0 + 1.0, "When a task looks too big, belief drops. Small finished steps build it back.",
                hi={"too": WARN, "big,": WARN, "steps": GREEN})


def s_value(c, t):
    t0 = SCENES[3][1]
    lt = t - t0
    c.cam(560, 1010, 1.05)
    room(c, t, window=False)
    win(c, 70, 560, 300, 330, t)
    plant(c, 90, GROUND, t)
    flip = prog(lt, 2.3, 0.7)
    cx, cy = 760, 960
    ang = flip * math.pi
    wscale = abs(math.cos(ang))
    if flip > 0.5:
        for i in range(14):  # golden rays
            a = math.radians(i * 360 / 14 + lt * 24)
            c.line([(cx + math.cos(a) * 160, cy + math.sin(a) * 160), (cx + math.cos(a) * 300, cy + math.sin(a) * 300)], 10, mix(WALL, GOLD, 0.5), cap=True)
        c.glow(cx, cy, 340, (255, 226, 140), 0.9)
    cw = 330 * max(wscale, 0.02)
    face = (214, 208, 196) if flip < 0.5 else (255, 253, 248)
    c.rrect(cx - cw / 2, cy - 210, cx + cw / 2, cy + 210, 30, fill=face, outline=INK if flip > 0.5 else MUTED, w=5)
    if wscale > 0.35:
        if flip < 0.5:
            c.text("TASK", cx, cy - 120, "bold", 44 * wscale, MUTED)
            for sx in (-1, 1):
                c.line([(cx + sx * 60 * wscale - 26 * wscale, cy - 30), (cx + sx * 60 * wscale + 26 * wscale, cy - 30)], 8, MUTED)
            c.line([(cx - 40 * wscale, cy + 70), (cx + 40 * wscale, cy + 70)], 8, MUTED)
            for j, zz in enumerate("zZz"):
                c.text(zz, cx - 90 * wscale + j * 22, cy - 250 - j * 36 - math.sin(lt * 3 + j) * 6, "head", 38 + j * 8, MUTED)
        else:
            icon_heart(c, cx, cy - 40, 90 * wscale, WARN)
            c.text("why it matters", cx, cy + 120, "head", 36 * wscale, INK)
            sparkle(c, cx - 170, cy - 170, 34, t, 0)
            sparkle(c, cx + 180, cy - 100, 28, t, 2)
            sparkle(c, cx + 140, cy + 160, 24, t, 4)
    if flip < 0.5:
        pose, eyes = pose_mix("stand", "shrug", prog(lt, 0.5, 0.5)), "normal"
    else:
        pose, eyes = pose_mix("shrug", "reach", prog(lt, 2.7, 0.5)), "stars" if flip > 0.9 else "normal"
    draw_person(c, 330, GROUND - 207, pose, ALEX, 1.25, t=t, gaze=(1, 0), shadow=(160, 120, 90), eyes=eyes)
    hud_title(c, t, t0 + 0.1, "2  VALUE", "Does it matter to me?")
    meter(c, 975, 800, lerp(0.28, 0.8, prog(lt, 2.6, 1.6)))
    hud_caption(c, t, t0 + 1.0, "The more a task matters, or feels rewarding, the stronger the pull. Boring tasks have low value.",
                hi={"matters,": GREEN, "rewarding,": GREEN, "Boring": WARN, "low": WARN}, size=44)


def s_impulse(c, t):
    t0 = SCENES[4][1]
    lt = t - t0
    k = prog(lt, 0.0, 5.0)
    room_scene(c, t, (lerp(560, 600, k), lerp(980, 960, k), lerp(1.0, 1.22, k)), calendar_day=28)
    typing = lt < 1.6
    laptop(c, 680, 1030, "typing" if typing or True else "blank", lines=int(lt * 5) if typing else 3, t=t)
    wake = prog(lt, 1.2, 0.4)
    shake = lt - 1.2 if lt > 1.2 else 0
    phone(c, 890, 1030 - 64, shake=shake, face=lt > 1.4, scale=0.8 + 0.25 * wake)
    pose = pose_mix("type", "sitlook", prog(lt, 1.6, 0.6))
    f = alex_seated(c, t, pose, gaze=(1, 0.5) if lt > 1.6 else (0.8, 0.1))
    kinds = ["heart", "chat", "star", "bolt"]
    for i, kind in enumerate(kinds):
        a = prog(lt, 1.8 + i * 0.35, 0.4, out_back)
        if a <= 0:
            continue
        ang = lt * 1.8 + i * math.pi / 2
        px = f["head"][0] + 40 + math.cos(ang) * (170 + i * 14)
        py = f["head"][1] - 40 + math.sin(ang) * 80 - 30
        c.circle(px, py, 38 * a, fill=WHITE, outline=INK, w=3)
        if kind == "heart":
            icon_heart(c, px, py - 2, 17 * a, WARN)
        elif kind == "chat":
            c.rrect(px - 17 * a, py - 12 * a, px + 17 * a, py + 10 * a, 6 * a, fill=(60, 130, 200))
        elif kind == "star":
            icon_star(c, px, py, 20 * a, GOLD)
        else:
            icon_bolt(c, px, py, 19 * a, WARN)
    hud_title(c, t, t0 + 0.1, "3  IMPULSIVENESS", "Why is my phone so tempting?", WARN)
    meter(c, 975, 800, lerp(0.72, 0.14, prog(lt, 1.8, 2.2)))
    hud_caption(c, t, t0 + 1.2,
                "The easier you are to distract, the lower your motivation. Steel links impulsiveness and distractibility to procrastination.",
                hi={"distract,": WARN, "lower": WARN, "impulsiveness": WARN}, size=42)


def hills(c, t, far=0.0):
    c.rrect(-1200, -600, 3200, 2800, 0, fill=SKY2)
    c.rrect(-1200, 900, 3200, 2800, 0, fill=(206, 232, 214))
    for i, (x, w, h, col) in enumerate(((100, 900, 200, (170, 214, 188)), (900, 1100, 280, (150, 204, 176)),
                                        (1700, 1300, 220, (170, 214, 188)), (2500, 1000, 260, (150, 204, 176)))):
        c.poly([(x - w / 2, 1000), (x, 1000 - h), (x + w / 2, 1000)], fill=col)
    c.rrect(-1200, 1000, 3200, 2800, 0, fill=(188, 222, 196))
    c.poly([(-1200, 1270), (3200, 1270), (3200, 1330), (-1200, 1330)], fill=(214, 190, 150))
    for i in range(3):
        cx = (200 + i * 700 + t * 14) % 2300 - 300
        for dx, dy, r in ((0, 0, 36), (40, 8, 30), (-38, 10, 26)):
            c.circle(cx + dx, 520 + i * 70 + dy, r, fill=WHITE)


def s_delay(c, t):
    t0 = SCENES[5][1]
    lt = t - t0
    k = prog(lt, 1.0, 4.2)
    c.cam(lerp(1040, 640, k), 1000, lerp(0.62, 1.0, k))
    hills(c, t)
    fx = lerp(1900, 800, k)
    ax = 340
    draw_person_walk = pose_mix("walkA", "walkB", (math.sin(lt * 6) + 1) / 2) if lt > 1.0 and k < 0.98 else "point"
    # flag + future Alex
    c.line([(fx, GROUND), (fx, GROUND - 330)], 10, INK)
    c.poly([(fx, GROUND - 330), (fx + 150, GROUND - 292), (fx, GROUND - 250)], fill=WARN)
    c.text("DEADLINE", fx + 56, GROUND - 292, "bold", 20, WHITE)
    draw_person(c, fx + 105, GROUND - 207 * 0.9, "wave", FUTURE, 0.9, t=t, gaze=(-1, 0), flip=True)
    # the pull: rope from Alex's hand to the flag
    pull = clamp(k)
    thick = lerp(4, 22, pull)
    hand_y = GROUND - 230
    sag = lerp(110, 10, pull)
    pts = [(ax + 110 + (fx - ax - 110) * u / 20, hand_y + math.sin(u / 20 * math.pi) * sag) for u in range(21)]
    c.line(pts, thick, mix((150, 150, 150), WARN, pull), cap=False)
    draw_person(c, ax, GROUND - 207, draw_person_walk, ALEX, 1.25, t=t, gaze=(1, -0.1), shadow=(150, 170, 140))
    label = "3 weeks away" if k < 0.6 else "tomorrow"
    with c.hud():
        pass
    c.text(label, fx - 10, GROUND + 70, "bold", 34 if k < 0.6 else 44, WARN if k > 0.6 else MUTED)
    hud_title(c, t, t0 + 0.1, "4  DELAY", "Why does the deadline feel so far away?", WARN)
    meter(c, 975, 800, lerp(0.14, 0.72, prog(lt, 1.0, 4.2)))
    hud_caption(c, t, t0 + 1.0, "The further away a reward or deadline feels, the weaker its pull.",
                hi={"further": WARN, "weaker": WARN}, size=48)


def s_tip(c, t):
    t0 = SCENES[6][1]
    lt = t - t0
    k = prog(lt, 0.0, 6.0)
    stamp = 22 if lt > 1.6 else 28
    room_scene(c, t, (lerp(700, 680, k), lerp(960, 980, k), lerp(1.0, 1.06, k)), calendar_day=stamp)
    pop = prog(lt, 1.6, 0.4, out_back)
    if lt > 1.6 and lt < 2.4:
        c.circle(585, 560, 160 * (1 - pop) + 10, outline=GREEN, w=6)
    laptop(c, 680, 1030, "typing", lines=int(lt * 4) % 9, t=t)
    phone(c, 890, 1030 - 64, scale=0.8)
    pose = pose_mix("sit", "type", prog(lt, 1.2, 0.5))
    f = alex_seated(c, t, pose, gaze=(1, 0.1))
    # Sam walks in and agrees
    sx = lerp(1350, 900, prog(lt, 2.2, 1.2, out_cubic))
    sp = "walkA" if lt < 3.4 else "wave"
    if lt > 2.2:
        draw_person(c, sx, GROUND - 207, pose_mix("walkA", "walkB", (math.sin(lt * 8) + 1) / 2) if lt < 3.4 else "wave", SAM, 1.25, t=t,
                    gaze=(-1, 0), flip=True, shadow=(160, 120, 90))
    sa = prog(lt, 3.0, 0.5, out_elastic)
    if sa > 0.02:
        speech(c, 470, 680, 470 * sa, 124 * sa, "Deal: Wednesday!", 40, tail=(f["head"][0] + 20, f["head"][1] - 76), a=clamp(sa))
    ya = prog(lt, 3.9, 0.5, out_elastic)
    if ya > 0.02:
        speech(c, 800, 790, 200 * ya, 100 * ya, "OK!", 46, tail=(sx - 20, GROUND - 207 - 250), a=clamp(ya))
    confetti(c, t, t0 + 4.3, 640, 800, seed=11) if lt > 4.3 else None
    hud_title(c, t, t0 + 0.1, "TRY THIS", "Shrink the delay")
    meter(c, 975, 800, lerp(0.4, 0.95, prog(lt, 1.6, 2.4)))
    with c.hud():
        a = prog(lt, 1.0, 0.5, out_cubic)
        c.rrect(70, 1380 + (1 - a) * 60, W - 70, 1650 + (1 - a) * 60, 34, fill=GREEN_SOFT, outline=GREEN, w=4)
    c.words("Pick one task. Set a deadline sooner than the real one, and tell someone.", W / 2, 1450, "bold", 44, 820, t,
            t0 + 1.2, INK, lh=1.3, per=0.08)
    with c.hud():
        c.text("Our suggestion, based on the “delay” part of the formula.", W / 2, 1618, "text", 28, MUTED)


def s_end(c, t):
    t0 = SCENES[7][1]
    lt = t - t0
    c.img.paste(gradient((247, 245, 238), (230, 238, 230)), (0, 0))
    c.d = ImageDraw.Draw(c.img)
    c.cam()
    a = prog(lt, 0.0, 0.6, out_back)
    with c.hud():
        r = 130 * a
        pts = [(W / 2, 520 - r), (W / 2 + r, 520), (W / 2, 520 + r), (W / 2 - r, 520), (W / 2, 520 - r)]
        c.line(pts, 12, GREEN)
        c.poly([(W / 2, 520 - r * 0.4), (W / 2 + r * 0.4, 520), (W / 2, 520 + r * 0.4), (W / 2 - r * 0.4, 520)], fill=GREEN)
    c.words("Which book fits why you put things off?", W / 2, 780, "head", 66, 880, t, t0 + 0.3, INK, lh=1.12, per=0.07)
    c.words("5 best books on procrastination", W / 2, 1010, "text", 46, 880, t, t0 + 1.3, MUTED)
    b = prog(lt, 2.0, 0.5, out_back)
    with c.hud():
        if b > 0:
            wd = c.tw("Link in bio", "bold", 50) + 110
            c.rrect(W / 2 - wd / 2 * b, 1110, W / 2 + wd / 2 * b, 1220, 14, fill=GREEN)
            if b > 0.9:
                c.text("Link in bio", W / 2, 1165, "bold", 50, WHITE)
    draw_person(c, 320, GROUND + 110 - 207 * 0.95, pose_mix("stand", "wave", prog(lt, 1.2, 0.5)), ALEX, 0.95, t=t, gaze=(1, 0))
    draw_person(c, 760, GROUND + 110 - 207 * 0.95, pose_mix("stand", "wave", prog(lt, 1.6, 0.5)), SAM, 0.95, t=t, gaze=(-1, 0), flip=True)
    with c.hud():
        c.line([(120, GROUND + 110), (960, GROUND + 110)], 6, MUTED)
        c.text("Alex and Sam are fictional characters. Based on public summaries of the book.", W / 2, 1640, "text", 26, MUTED)


FUNCS = [s_hook, s_formula, s_expect, s_value, s_impulse, s_delay, s_tip, s_end]


def draw_scene(idx, t):
    c = Canvas()
    FUNCS[idx](c, t)
    if idx != len(FUNCS) - 1:
        hud_footer(c)
    return c.frame()


def draw_at(t):
    i = scene_at(t)
    img = draw_scene(i, t)
    if i > 0 and t - SCENES[i][1] < TRANS:
        prev = draw_scene(i - 1, t)
        u = (t - SCENES[i][1]) / TRANS
        focus = (W * 0.5, H * 0.52)
        img = iris_wipe(prev, img, u, *focus)
    return img


def frame(i):
    return draw_at(i / FPS)


def main():
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)
    if "--still" in sys.argv:
        t = float(sys.argv[sys.argv.index("--still") + 1])
        draw_at(t).save(out_dir / f"v2-still-{t:g}.png")
        print("saved", t)
    elif "--sheet" in sys.argv:
        ts = [1.0, 4.4, 7.0, 10.5, 15.0, 18.3, 21.0, 24.2, 27.4, 30.5, 34.0, 37.3, 40.0, 43.5, 46.0]
        ims = [draw_at(t).resize((270, 480)) for t in ts]
        cols = 8
        sheet = Image.new("RGB", (cols * 275, 2 * 485), "white")
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 275, (i // cols) * 485))
        sheet.save(out_dir / "v2-sheet.png")
        print("sheet saved")
    else:
        from audio import build_audio
        wav = out_dir / "procrastination-v2.wav"
        build_audio(wav, TOTAL, SCENES)
        target = out_dir / "procrastination-equation-v2.mp4"
        n = render_video(frame, TOTAL, target, audio=wav)
        print("rendered", n, "frames ->", target)


if __name__ == "__main__":
    main()
