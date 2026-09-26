"""Generate Pinterest pin images (1000x1500) and copy-paste text for GrowthLane articles.

Each article has a spec file in pipeline/pins/<slug>.json. Run from the repo root:
    python pipeline/make_pins.py            # every spec whose images or text file are missing
    python pipeline/make_pins.py --force    # regenerate everything
    python pipeline/make_pins.py <slug>     # one article only

Output: assets/pins/<slug>-pin-<x>.png and assets/pins/<slug>.txt (title, description,
destination link with UTM tags, alt text). Posting to Pinterest stays manual.
"""
import json
import re
import sys
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


def make_pin(filename, eyebrow, headline, subtext, facts, cta="Read the full review at growthlane blog"):
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
    draw.text((margin, H - 60), cta, font=cta_font, fill="#e8f0ec")

    out_path = OUT_DIR / filename
    img.save(out_path, "PNG")
    print(f"Saved {out_path}")


ROOT = Path(__file__).parent.parent
SPEC_DIR = Path(__file__).parent / "pins"


def site_base():
    """Public site URL: pipeline/cloudflare.yml overrides _config.yml (the live host)."""
    def read(path):
        cfg = path.read_text(encoding="utf-8")
        url = re.search(r'^url:\s*"?([^"\n]+)"?', cfg, re.M)
        baseurl = re.search(r'^baseurl:\s*"?([^"\n]*)"?', cfg, re.M)
        return url.group(1).strip() if url else None, baseurl.group(1).strip() if baseurl else None

    url, baseurl = read(ROOT / "_config.yml")
    override = Path(__file__).parent / "cloudflare.yml"
    if override.exists():
        o_url, o_base = read(override)
        url = o_url or url
        baseurl = o_base if o_base is not None else baseurl
    return url.rstrip("/") + (baseurl or "").rstrip("/")


def post_url(post_file):
    """Build the public URL from a post filename (permalink /:year/:month/:day/:title/)."""
    name = Path(post_file).stem  # 2026-09-25-some-title
    y, m, d, title = name.split("-", 3)
    return f"{site_base()}/{y}/{m}/{d}/{title}/"


def build_text(spec):
    url = post_url(spec["post"])
    utm = f"?utm_source=pinterest&utm_medium=social&utm_campaign={spec['slug']}"
    lines = [f"Article: {spec['post']}", f"Destination link (paste into the pin): {url}{utm}", ""]
    for pin in spec["pins"]:
        lines += [
            f"--- Pin {pin['suffix'].upper()} ({spec['slug']}-pin-{pin['suffix']}.png) ---",
            f"Title: {pin['pinterest_title']}",
            f"Alt text: {pin['alt_text']}",
            "",
        ]
    lines += ["Description (same for both pins):", spec["pinterest_description"], "", spec["disclosure_line"], ""]
    return "\n".join(lines)


def run_spec(path, force):
    spec = json.loads(path.read_text(encoding="utf-8"))
    slug = spec["slug"]
    facts = [tuple(f) for f in spec["facts"]]
    made = False
    for pin in spec["pins"]:
        png = f"{slug}-pin-{pin['suffix']}.png"
        if force or not (OUT_DIR / png).exists():
            make_pin(png, pin["eyebrow"], pin["headline"], pin["subtext"], facts, spec.get("cta", "Read the full review at growthlane blog"))
            made = True
    txt = OUT_DIR / f"{slug}.txt"
    if force or not txt.exists():
        txt.write_text(build_text(spec), encoding="utf-8")
        print(f"Saved {txt}")
        made = True
    if not made:
        print(f"{slug}: up to date")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    specs = sorted(SPEC_DIR.glob("*.json"))
    if args:
        specs = [p for p in specs if p.stem in args]
    for spec_path in specs:
        run_spec(spec_path, force)
