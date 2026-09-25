"""Generate Pinterest pin images (1000x1500) for a GrowthLane article."""
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 1500

BG = "#f7f5ee"
TEXT = "#1a1a1a"
MUTED = "#5f6368"
ACCENT = "#1d5f4a"

FONT_DIR = Path("C:/Windows/Fonts")
HEADLINE_FONT = FONT_DIR / "GeorgiaPro-Bold.ttf"
EYEBROW_FONT = FONT_DIR / "arialbd.ttf"
SUB_FONT = FONT_DIR / "arial.ttf"
LOGO_FONT = FONT_DIR / "GeorgiaPro-Bold.ttf"

OUT_DIR = Path(__file__).parent.parent / "assets" / "pins"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def wrap_and_draw(draw, text, font, max_width, start_y, fill, line_spacing=1.25, align="left", x_margin=70):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    ascent, descent = font.getmetrics()
    line_height = int((ascent + descent) * line_spacing)
    y = start_y
    for line in lines:
        line_width = draw.textlength(line, font=font)
        if align == "center":
            x = (W - line_width) / 2
        else:
            x = x_margin
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def make_pin(filename, eyebrow, headline, subtext, facts):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    margin = 70

    # Top accent bar
    draw.rectangle([0, 0, W, 14], fill=ACCENT)

    # Eyebrow tag
    eyebrow_font = ImageFont.truetype(str(EYEBROW_FONT), 30)
    draw.text((margin, 110), eyebrow.upper(), font=eyebrow_font, fill=ACCENT)

    # Headline
    headline_font = ImageFont.truetype(str(HEADLINE_FONT), 74)
    y = wrap_and_draw(draw, headline, headline_font, W - 2 * margin, 175, TEXT, line_spacing=1.12)

    # Divider
    y += 30
    draw.line([(margin, y), (margin + 90, y)], fill=ACCENT, width=6)
    y += 50

    # Subtext
    sub_font = ImageFont.truetype(str(SUB_FONT), 38)
    y = wrap_and_draw(draw, subtext, sub_font, W - 2 * margin, y, MUTED, line_spacing=1.35)

    # Quick-facts box in the remaining middle space
    box_top = y + 60
    box_bottom = H - 220
    draw.rectangle([margin, box_top, W - margin, box_bottom], outline=ACCENT, width=3)

    fact_font_label = ImageFont.truetype(str(EYEBROW_FONT), 30)
    fact_font_value = ImageFont.truetype(str(HEADLINE_FONT), 44)
    row_h = (box_bottom - box_top) / len(facts)
    for i, (label, value) in enumerate(facts):
        row_y = box_top + i * row_h
        draw.text((margin + 35, row_y + row_h * 0.22), label.upper(), font=fact_font_label, fill=MUTED)
        draw.text((margin + 35, row_y + row_h * 0.48), value, font=fact_font_value, fill=TEXT)
        if i > 0:
            draw.line([(margin, row_y), (W - margin, row_y)], fill="#e5e0d5", width=2)

    # Bottom wordmark + CTA
    logo_font = ImageFont.truetype(str(LOGO_FONT), 44)
    draw.rectangle([0, H - 160, W, H], fill=ACCENT)
    draw.text((margin, H - 115), "GrowthLane", font=logo_font, fill="#ffffff")
    cta_font = ImageFont.truetype(str(SUB_FONT), 30)
    draw.text((margin, H - 60), "Read the full review at growthlane blog", font=cta_font, fill="#e8f0ec")

    out_path = OUT_DIR / filename
    img.save(out_path, "PNG")
    print(f"Saved {out_path}")


FACTS = [
    ("Price", "$97 one-time"),
    ("Guarantee", "60 days, no questions"),
    ("Inside", "27 audios + 4 videos"),
]

if __name__ == "__main__":
    make_pin(
        "life-optimization-review-pin-a.png",
        eyebrow="Honest Review",
        headline="Is There Actually a Real System for Getting Your Life Together?",
        subtext="We reviewed a 30-year coach's personal development program \u2014 the good and the unclear parts.",
        facts=FACTS,
    )

    make_pin(
        "life-optimization-review-pin-b.png",
        eyebrow="Honest Review",
        headline="A Coaching Program With 2,000+ Real Clients, Reviewed",
        subtext="What's actually inside, what it costs, and who it's really for.",
        facts=FACTS,
    )
