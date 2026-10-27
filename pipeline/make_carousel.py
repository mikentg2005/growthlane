"""Build an Instagram carousel (1080x1350) for a GrowthLane book-list article.

Run from the repo root:  python pipeline/make_carousel.py
Output: pipeline/social/instagram/habits/slide-1.png ... plus caption.txt
Text comes from the article's own Best for / Downside lines; nothing is invented.
"""
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "social" / "instagram" / "habits"
W, H = 1080, 1350
PAPER, INK, MUTED, GREEN = "#f7f5ee", "#17201b", "#56635b", "#1d5f4a"
WARN, WARN_SOFT, GREEN_SOFT = "#9a4a2b", "#f3e4dc", "#e3eee8"

F = Path("C:/Windows/Fonts")
HEAD, LABEL, TEXT = F / "GeorgiaPro-Bold.ttf", F / "arialbd.ttf", F / "arial.ttf"


def font(path, size):
    return ImageFont.truetype(str(path), size)


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def diamond(d, cx, cy, r, color, stroke=5):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=color, width=stroke)
    ri = r * 0.38
    d.polygon([(cx, cy - ri), (cx + ri, cy), (cx, cy + ri), (cx - ri, cy)], fill=color)


def base():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=GREEN)
    return img, d


def footer(d, n, total):
    diamond(d, 78, H - 70, 18, GREEN, 3)
    d.text((110, H - 90), "GrowthLane", font=font(HEAD, 34), fill=INK)
    t = f"{n}/{total}"
    f = font(LABEL, 28)
    d.text((W - 70 - d.textlength(t, font=f), H - 86), t, font=f, fill=MUTED)


SLIDES = [
    ("1847941834", "Atomic Habits", "James Clear",
     "readers who want one complete, practical framework rather than scattered tips.",
     "so widely discussed elsewhere that parts may feel familiar."),
    ("081298160X", "The Power of Habit", "Charles Duhigg",
     "readers who want to understand the mechanism before trying to change anything.",
     "it explains the \u201cwhy\u201d better than it hands you a \u201chow.\u201d"),
    ("0753553244", "Tiny Habits", "BJ Fogg",
     "anyone who failed at ambitious habit goals and wants to start absurdly small.",
     "celebrating every tiny win can feel a little forced at first."),
    ("1399805789", "The Compound Effect", "Darren Hardy",
     "readers who like a direct, no-nonsense style and want the case for small habits made plainly.",
     "lighter on specific technique; more mindset than mechanism."),
    ("1444769014", "Better Than Before", "Gretchen Rubin",
     "readers whose generic habit method did not fit them personally.",
     "with so many strategies on offer, it can feel less focused."),
]
TOTAL = len(SLIDES) + 2


def cover_slide():
    img, d = base()
    d.text((70, 90), "BOOK LIST", font=font(LABEL, 34), fill=GREEN)
    f = font(HEAD, 104)
    y = 190
    for line in wrap(d, "5 best books on building better habits", f, W - 140):
        d.text((70, y), line, font=f, fill=INK)
        y += 124
    d.rectangle([70, y + 20, 70 + 120, y + 28], fill=GREEN)
    fs = font(TEXT, 44)
    y += 70
    for line in wrap(d, "And which one to start with, based on how you think.", fs, W - 140):
        d.text((70, y), line, font=fs, fill=MUTED)
        y += 60
    # row of the five covers
    x, cw, ch, gap = 70, 170, 255, 22
    y0 = H - 470
    for asin, *_ in SLIDES:
        c = Image.open(ROOT / "assets" / "books" / f"{asin}.jpg").convert("RGB")
        c = c.resize((cw, ch))
        img.paste(c, (x, y0))
        x += cw + gap
    d.text((70, H - 175), "Swipe  \u2192", font=font(LABEL, 40), fill=GREEN)
    footer(d, 1, TOTAL)
    return img


def book_slide(n, asin, title, author, best, down):
    img, d = base()
    c = Image.open(ROOT / "assets" / "books" / f"{asin}.jpg").convert("RGB")
    ch = 470
    cw = int(c.width * ch / c.height)
    c = c.resize((cw, ch))
    img.paste(c, (70, 90))
    tx = 70 + cw + 50
    d.text((tx, 100), f"BOOK {n - 1} OF {len(SLIDES)}", font=font(LABEL, 30), fill=GREEN)
    f = font(HEAD, 64)
    y = 160
    for line in wrap(d, title, f, W - tx - 60):
        d.text((tx, y), line, font=f, fill=INK)
        y += 78
    d.text((tx, y + 8), author, font=font(TEXT, 40), fill=MUTED)

    def box(y, label, body, bg, fg):
        fb = font(TEXT, 42)
        lines = wrap(d, body, fb, W - 140 - 60)
        h = 100 + len(lines) * 58
        d.rounded_rectangle([70, y, W - 70, y + h], radius=14, fill=bg)
        d.text((100, y + 28), label, font=font(LABEL, 30), fill=fg)
        yy = y + 78
        for ln in lines:
            d.text((100, yy), ln, font=fb, fill=INK)
            yy += 58
        return y + h

    y = box(640, "BEST FOR", body_cap(best), GREEN_SOFT, GREEN)
    box(y + 30, "DOWNSIDE", body_cap(down), WARN_SOFT, WARN)
    footer(d, n, TOTAL)
    return img


def body_cap(s):
    return s[0].upper() + s[1:]


def last_slide():
    img, d = base()
    diamond(d, W // 2, 330, 150, GREEN, 12)
    f = font(HEAD, 86)
    y = 560
    for line in wrap(d, "Read the honest reviews", f, W - 160):
        w = d.textlength(line, font=f)
        d.text(((W - w) / 2, y), line, font=f, fill=INK)
        y += 104
    fs = font(TEXT, 44)
    for line in wrap(d, "Who each book is for, where it falls short, and which to read first.", fs, W - 200):
        w = d.textlength(line, font=fs)
        d.text(((W - w) / 2, y + 30), line, font=fs, fill=MUTED)
        y += 60
    fb = font(LABEL, 46)
    t = "Link in bio"
    w = d.textlength(t, font=fb)
    d.rounded_rectangle([(W - w) / 2 - 50, y + 100, (W + w) / 2 + 50, y + 200], radius=10, fill=GREEN)
    d.text(((W - w) / 2, y + 125), t, font=fb, fill="white")
    fn = font(TEXT, 28)
    note = "Some links on GrowthLane are affiliate links."
    d.text(((W - d.textlength(note, font=fn)) / 2, H - 170), note, font=fn, fill=MUTED)
    footer(d, TOTAL, TOTAL)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [cover_slide()]
    for i, s in enumerate(SLIDES, start=2):
        slides.append(book_slide(i, *s))
    slides.append(last_slide())
    for i, im in enumerate(slides, start=1):
        im.save(OUT / f"slide-{i}.png", "PNG", optimize=True)
        print("wrote", OUT / f"slide-{i}.png")
    # contact sheet for a quick look
    sheet = Image.new("RGB", (len(slides) * 270, 340), "white")
    for i, im in enumerate(slides):
        t = im.copy()
        t.thumbnail((260, 330))
        sheet.paste(t, (i * 270, 5))
    sheet.save(OUT / "contact-sheet.png")


if __name__ == "__main__":
    main()
