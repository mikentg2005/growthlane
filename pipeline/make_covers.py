"""Generate share-preview covers (1200x630) and pin thumbnails for GrowthLane posts.

Run from the repo root:
    python pipeline/make_covers.py            # create anything missing
    python pipeline/make_covers.py --force    # regenerate everything

For every post in _posts it writes assets/covers/<slug>.png, used as the og:image
(link previews on Telegram, WhatsApp, X, Pinterest and so on).
For every pin spec in pipeline/pins/*.json it writes a small thumbnail of pin A to
assets/pins/thumbs/<spec-slug>-pin-a.jpg, used by the "Save to Pinterest" block.
It also adds the matching image / pin_image / pin_thumb lines to each post's front
matter when they are missing.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
SPECS = Path(__file__).resolve().parent / "pins"
COVERS = ROOT / "assets" / "covers"
THUMBS = ROOT / "assets" / "pins" / "thumbs"

W, H = 1200, 630
PAPER = "#f7f5ee"
INK = "#17201b"
MUTED = "#56635b"
GREEN = "#1d5f4a"

FONT_DIR = Path("C:/Windows/Fonts")
HEAD_FONT = FONT_DIR / "GeorgiaPro-Bold.ttf"
LABEL_FONT = FONT_DIR / "arialbd.ttf"
TEXT_FONT = FONT_DIR / "arial.ttf"

FORCE = "--force" in sys.argv


def read_front_matter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm, text


def wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def short_title(title):
    return title.split(" (")[0].strip()


def draw_mark(draw, cx, cy, r, color_outer, color_inner, stroke):
    """The diamond brand mark used in the favicon."""
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    draw.polygon(pts, outline=color_outer, width=stroke)
    ri = r * 0.38
    draw.polygon([(cx, cy - ri), (cx + ri, cy), (cx, cy + ri), (cx - ri, cy)], fill=color_inner)


def make_cover(slug, title, category, basis):
    out = COVERS / f"{slug}.png"
    if out.exists() and not FORCE:
        return False
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # right brand panel
    panel_x = 880
    d.rectangle([panel_x, 0, W, H], fill=GREEN)
    draw_mark(d, panel_x + (W - panel_x) // 2, 250, 95, PAPER, PAPER, 12)
    wm = ImageFont.truetype(str(HEAD_FONT), 40)
    wm_w = d.textlength("GrowthLane", font=wm)
    d.text((panel_x + (W - panel_x - wm_w) / 2, 400), "GrowthLane", font=wm, fill="#ffffff")
    tag = ImageFont.truetype(str(TEXT_FONT), 22)
    tag_text = "Honest reviews. No hype."
    tag_w = d.textlength(tag_text, font=tag)
    d.text((panel_x + (W - panel_x - tag_w) / 2, 460), tag_text, font=tag, fill="#cfe3da")

    # top rule
    d.rectangle([0, 0, panel_x, 12], fill=GREEN)

    margin = 70
    label_font = ImageFont.truetype(str(LABEL_FONT), 26)
    cat = category.upper()
    d.text((margin, 62), cat, font=label_font, fill=GREEN)
    cat_w = d.textlength(cat, font=label_font)

    # basis chip
    chip_text = "FIRST-HAND" if basis == "first-hand" else "RESEARCH-BASED"
    chip_font = ImageFont.truetype(str(LABEL_FONT), 20)
    cw = d.textlength(chip_text, font=chip_font)
    cx = margin + cat_w + 26
    box = [cx, 56, cx + cw + 28, 56 + 40]
    if basis == "first-hand":
        d.rectangle(box, fill=GREEN)
        d.text((cx + 14, 66), chip_text, font=chip_font, fill="#ffffff")
    else:
        d.rectangle(box, outline=MUTED, width=2)
        d.text((cx + 14, 66), chip_text, font=chip_font, fill=MUTED)

    # headline: biggest size that fits in at most 4 lines
    text_w = panel_x - margin - 60
    headline = short_title(title)
    for size in range(76, 40, -2):
        f = ImageFont.truetype(str(HEAD_FONT), size)
        lines = wrap(d, headline, f, text_w)
        asc, desc = f.getmetrics()
        lh = int((asc + desc) * 1.08)
        if len(lines) <= 4 and 130 + lh * len(lines) <= H - 110:
            break
    y = 135
    for line in lines:
        d.text((margin, y), line, font=f, fill=INK)
        y += lh

    # accent underline under the headline
    d.rectangle([margin, y + 22, margin + 90, y + 28], fill=GREEN)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"cover  {out.relative_to(ROOT)}")
    return True


def make_thumb(spec_slug):
    src = ROOT / "assets" / "pins" / f"{spec_slug}-pin-a.png"
    out = THUMBS / f"{spec_slug}-pin-a.jpg"
    if not src.exists() or (out.exists() and not FORCE):
        return False
    img = Image.open(src).convert("RGB")
    img.thumbnail((360, 540))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=84, optimize=True)
    print(f"thumb  {out.relative_to(ROOT)}")
    return True


def ensure_front_matter(path, additions):
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    head, rest = text[:end], text[end:]
    changed = False
    for key, value in additions.items():
        if re.search(rf"^{key}:", head, re.M):
            continue
        head += f"\n{key}: {value}"
        changed = True
    if changed:
        path.write_text(head + rest, encoding="utf-8", newline="\n")
        print(f"front matter updated: {path.name}")


def main():
    post_to_spec = {}
    for spec_path in sorted(SPECS.glob("*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        post_to_spec[Path(spec["post"]).name] = spec["slug"]
        make_thumb(spec["slug"])

    for post in sorted(POSTS.glob("*.md")):
        fm, _ = read_front_matter(post)
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", post.stem)
        make_cover(slug, fm.get("title", slug), fm.get("category", "Article"), fm.get("basis", "research"))
        additions = {"image": f"/assets/covers/{slug}.png"}
        spec_slug = post_to_spec.get(post.name)
        if spec_slug:
            additions["pin_image"] = f"/assets/pins/{spec_slug}-pin-a.png"
            additions["pin_thumb"] = f"/assets/pins/thumbs/{spec_slug}-pin-a.jpg"
        ensure_front_matter(post, additions)


if __name__ == "__main__":
    main()
