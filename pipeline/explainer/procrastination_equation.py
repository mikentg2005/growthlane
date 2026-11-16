"""Explainer video: "The Procrastination Equation" (about 40 s, 1080x1920, no voice).

Run from the repo root:
    python pipeline/explainer/procrastination_equation.py            # full video
    python pipeline/explainer/procrastination_equation.py --still 12.5   # one frame, for checking

Everything said on screen comes from the sources listed in the article
_posts/2026-11-13-best-books-on-procrastination.md (Steel's formula as summarised in
public outlines, Publishers Weekly, Straight.com). The last tip is labelled as ours.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import *  # noqa: E402,F403

SCENES = [  # (name, start, end)
    ("hook", 0.0, 4.6),
    ("formula", 4.6, 11.0),
    ("expectancy", 11.0, 16.6),
    ("value", 16.6, 22.0),
    ("impulse", 22.0, 27.6),
    ("delay", 27.6, 33.4),
    ("tip", 33.4, 38.0),
    ("end", 38.0, 42.0),
]
TOTAL = SCENES[-1][2]
GROUND = 1270
CAP_Y = 1420


def header(c, t, t0, label, title, color=GREEN):
    a = prog(t, t0, 0.4)
    if label:
        pill(c, W / 2, 215 + (1 - a) * 20, label, mix(PAPER, color, a))
    c.reveal(title, W / 2, 280, font("head", 76), 900, t, t0 + 0.15, INK, lh=1.15)


def caption(c, t, t0, text, size=46, color=MUTED):
    c.reveal(text, W / 2, CAP_Y, font("text", size), 900, t, t0, color, lh=1.38, per=0.07)


def desk(c, x0, x1, top):
    c.rrect(x0, top, x1, top + 22, 8, fill=(207, 202, 186))
    c.line([(x0 + 30, top + 22), (x0 + 30, GROUND)], 14, (170, 165, 150))
    c.line([(x1 - 30, top + 22), (x1 - 30, GROUND)], 14, (170, 165, 150))


def chair(c, x, seat_y):
    c.line([(x - 70, seat_y + 12), (x + 30, seat_y + 12)], 16, (170, 165, 150))
    c.line([(x - 70, seat_y + 12), (x - 70, seat_y - 170)], 14, (170, 165, 150))
    c.line([(x - 55, seat_y + 12), (x - 55, GROUND)], 12, (170, 165, 150))


def laptop(c, x, top):
    c.rrect(x - 90, top - 130, x + 90, top - 4, 10, fill=INK)
    c.rrect(x - 80, top - 120, x + 80, top - 14, 6, fill=(200, 215, 208))
    c.rrect(x - 110, top - 6, x + 110, top + 2, 4, fill=(120, 126, 122))


def sit_figure(c, x, pose, scale=1.3):
    seat = GROUND - SH * scale
    chair(c, x, seat)
    return draw_figure(c, x, seat, pose, scale)


# ---------- scenes ----------
def s_hook(c, t):
    header(c, t, 0.1, None, "Why do we put things off?")
    desk(c, 540, 930, 1060)
    laptop(c, 740, 1060)
    pose = pose_mix("sit", "sitlook", prog(t, 2.0, 0.6))
    f = sit_figure(c, 380, pose)
    bob = math.sin(t * 3) * 6
    a = prog(t, 0.9, 0.4)
    if a > 0:
        bubble(c, 640, 640 + bob, 470, 150, tail_to=(f["head"][0] + 30, f["head"][1] - 70))
        c.text("I'll start later…", 640, 640 + bob, font("head", 46), mix(PAPER, INK, a), "mm")
    caption(c, t, 2.0, "It is usually blamed on laziness. Researchers see it differently.")


def s_formula(c, t):
    t0 = 4.6
    lt = t - t0
    header(c, t, t0, "THE FORMULA", "One research-based equation")
    f1, f2 = font("head", 84), font("head", 74)
    a = prog(t, t0 + 0.8, 0.5)
    c.text("Motivation  =", W / 2, 720, f1, mix(PAPER, INK, a), "mm")
    rows = [(880, [("Expectancy", GREEN, 1.6), ("×", MUTED, 1.6), ("Value", GREEN, 2.0)]),
            (1090, [("Impulsiveness", WARN, 2.8), ("×", MUTED, 2.8), ("Delay", WARN, 3.2)])]
    for y, items in rows:
        fonts = [f1 if lab == "×" else f2 for lab, _, _ in items]
        gap = 36
        total = sum(c.tw(lab, fo) for (lab, _, _), fo in zip(items, fonts)) + gap * (len(items) - 1)
        x = W / 2 - total / 2
        for (lab, col, when), fo in zip(items, fonts):
            wd = c.tw(lab, fo)
            a = prog(lt, when, 0.45)
            if a > 0:
                c.text(lab, x + wd / 2, y + (1 - a) * 16, fo, mix(PAPER, col, a), "mm")
            x += wd + gap
    bar = prog(lt, 2.3, 0.5)
    c.line([(W / 2 - 380, 985), (W / 2 - 380 + 760 * bar, 985)], 8, INK)
    caption(c, t, t0 + 4.0,
            "In plain words: you start when you believe you can, it matters to you, and you are not easily distracted.",
            size=44)


def s_expectancy(c, t):
    t0 = 11.0
    lt = t - t0
    header(c, t, t0, "1  EXPECTANCY", "Can I actually do this?")
    ground(c, GROUND)
    k = prog(lt, 2.4, 1.2)
    mountain(c, 700, GROUND, 520, lerp(430, 120, k))
    pose = pose_mix("slump", "reach", prog(lt, 2.5, 0.8))
    draw_figure(c, 290, GROUND - (TH + SH) * 1.35, pose, 1.35)
    meter(c, 960, 800, lerp(0.22, 0.82, prog(lt, 2.5, 1.2)))
    caption(c, t, t0 + 1.4,
            "When a task looks too big, belief drops. The book suggests small wins: each finished step makes the next one feel possible.",
            size=44)


def s_value(c, t):
    t0 = 16.6
    lt = t - t0
    header(c, t, t0, "2  VALUE", "Does it matter to me?")
    ground(c, GROUND)
    k = prog(lt, 2.4, 0.8)
    bx, by = 700, GROUND - 160
    c.rrect(bx - 150, by - 150, bx + 150, by + 150, 30, fill=mix((226, 222, 210), GREEN_SOFT, k),
            outline=mix(MUTED, GREEN, k), w=6)
    c.text("TASK", bx, by - 60, font("bold", 40), mix(MUTED, GREEN, k), "mm")
    # face on the task: bored -> interested
    for sx in (-1, 1):
        c.circle(bx + sx * 45, by + 10, 9, fill=mix(MUTED, GREEN, k))
    if k < 0.5:
        c.line([(bx - 45, by + 80), (bx + 45, by + 80)], 7, MUTED)
    else:
        c.arc(bx, by + 50, 50, 20, 160, 7, GREEN)
    if k > 0.3:  # a star appears: "why it matters"
        sx, sy, r = bx + 150, by - 170, 44 * ease((k - 0.3) / 0.7)
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((sx + rr * math.cos(ang), sy + rr * math.sin(ang)))
        c.poly(pts, fill=GOLD)
    pose = pose_mix("shrug", "reach", prog(lt, 2.5, 0.8))
    draw_figure(c, 290, GROUND - (TH + SH) * 1.35, pose, 1.35)
    meter(c, 960, 800, lerp(0.3, 0.72, prog(lt, 2.5, 1.0)))
    caption(c, t, t0 + 1.2,
            "The more a task matters, or feels rewarding, the stronger the pull. A boring or unpleasant task has low value.",
            size=44)


def s_impulse(c, t):
    t0 = 22.0
    lt = t - t0
    header(c, t, t0, "3  IMPULSIVENESS", "Why is my phone so tempting?", WARN)
    desk(c, 540, 930, 1060)
    laptop(c, 700, 1060)
    shake = lt if 1.0 < lt < 4.6 else 0
    phone(c, 860, 1060 - 74, shake)
    pose = pose_mix("sit", "sitlook", prog(lt, 1.3, 0.6))
    sit_figure(c, 380, pose)
    for i in range(3):  # notification pings
        a = clamp((lt - 1.0 - i * 0.35) / 0.4)
        if a > 0 and lt < 4.6:
            r = 24 * ease(a)
            c.circle(840 + i * 34, 900 - i * 40 - a * 30, r, fill=WARN)
            c.text("!", 840 + i * 34, 900 - i * 40 - a * 30, font("bold", 30), (255, 255, 255), "mm")
    meter(c, 960, 800, lerp(0.7, 0.18, prog(lt, 1.4, 1.4)))
    caption(c, t, t0 + 1.2,
            "The easier you are to distract, the lower your motivation. Steel's review links impulsiveness and distractibility to procrastination.",
            size=42)


def s_delay(c, t):
    t0 = 27.6
    lt = t - t0
    header(c, t, t0, "4  DELAY", "Why does the deadline feel so far away?", WARN)
    ground(c, GROUND)
    flag(c, 860, GROUND, 230, "deadline")
    walk = prog(lt, 0.8, 3.6)
    x = lerp(150, 590, walk)
    cyc = math.sin(lt * 7.0)
    pose = pose_mix("walkA", "walkB", (cyc + 1) / 2) if walk < 0.99 else "reach"
    draw_figure(c, x, GROUND - (TH + SH) * 1.35 - 6, pose, 1.35)
    # distance marker
    c.line([(x + 90, GROUND + 70), (850, GROUND + 70)], 5, WARN)
    c.text("far" if walk < 0.5 else "closer", (x + 90 + 850) / 2, GROUND + 112, font("bold", 28), WARN, "mm")
    meter(c, 960, 800, lerp(0.15, 0.62, walk))
    caption(c, t, t0 + 1.0, "The further away a reward or deadline feels, the weaker its pull.", size=48)


def s_tip(c, t):
    t0 = 33.4
    lt = t - t0
    header(c, t, t0, "TRY THIS", "Shrink the delay")
    ground(c, GROUND)
    flag(c, 640, GROUND, 250, "earlier deadline", GREEN)
    pose = pose_mix("reach", "cheer", prog(lt, 1.6, 0.6))
    draw_figure(c, 330, GROUND - (TH + SH) * 1.35, pose, 1.35)
    meter(c, 960, 800, lerp(0.5, 0.9, prog(lt, 1.0, 1.2)))
    c.rrect(80, 1400, 1000, 1640, 28, fill=GREEN_SOFT, outline=GREEN, w=4)
    c.reveal("Pick one task. Set a deadline sooner than the real one, and tell someone.", W / 2, 1440,
             font("bold", 44), 820, t, t0 + 0.8, INK, lh=1.32)
    c.text("Our suggestion, based on the “delay” part of the formula.", W / 2, 1600, font("text", 28), MUTED, "mm")


def s_end(c, t):
    t0 = 38.0
    a = prog(t, t0, 0.5)
    diamond(c, W / 2, 640, 150 * (0.8 + 0.2 * a), GREEN, 12)
    c.reveal("Which book fits why you put things off?", W / 2, 880, font("head", 70), 880, t, t0 + 0.3, INK, lh=1.15)
    c.reveal("5 best books on procrastination", W / 2, 1180, font("text", 46), 880, t, t0 + 1.4, MUTED)
    b = prog(t, t0 + 2.0, 0.4)
    if b > 0:
        f = font("bold", 48)
        wd = c.tw("Link in bio", f)
        c.rrect(W / 2 - wd / 2 - 54, 1290, W / 2 + wd / 2 + 54, 1390, 12, fill=mix(PAPER, GREEN, b))
        c.text("Link in bio", W / 2, 1340, f, mix(PAPER, (255, 255, 255), b), "mm")
    c.text("Based on public summaries of the book.", W / 2, 1500, font("text", 28), MUTED, "mm")


FUNCS = {"hook": s_hook, "formula": s_formula, "expectancy": s_expectancy, "value": s_value,
         "impulse": s_impulse, "delay": s_delay, "tip": s_tip, "end": s_end}


def draw_at(t):
    c = Canvas()
    c.rrect(0, 0, W, 14, 0, fill=GREEN)
    for name, a, b in SCENES:
        if a <= t < b or (t >= TOTAL and name == "end"):
            FUNCS[name](c, t)
            if name != "end":
                footer(c)
            fade = clamp((t - a) / 0.25)
            if fade < 1 and name != "hook":
                pass
            break
    return c.frame()


def frame(i):
    return draw_at(i / FPS)


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(exist_ok=True)
    if "--still" in sys.argv:
        t = float(sys.argv[sys.argv.index("--still") + 1])
        draw_at(t).save(out_dir / f"still-{t:g}.png")
        print("saved", out_dir / f"still-{t:g}.png")
    else:
        target = out_dir / "procrastination-equation.mp4"
        n = render_video(frame, TOTAL, target)
        print("rendered", n, "frames ->", target)
