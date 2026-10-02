"""Pre-publish checks for GrowthLane posts.

Run from the repo root:  python pipeline/lint_posts.py
Checks every file in _posts (and _drafts, as warnings only for missing dates).
Exit code 1 if any ERROR is found, so it can gate a commit.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST_DIRS = [ROOT / "_posts", ROOT / "_drafts"]

AMAZON_TAG = "growthlane01-21"
CLICKBANK_TID_PREFIX = "growthlane_"

AMAZON_HOST = re.compile(r"https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.to|a\.co)/", re.I)
CLICKBANK_HOST = re.compile(r"https?://[^\s\"')]*\.hop\.clickbank\.net", re.I)
ANCHOR = re.compile(r"<a\s[^>]*>", re.I)
HREF = re.compile(r"href=\"([^\"]+)\"", re.I)
REL = re.compile(r"rel=\"([^\"]*)\"", re.I)
MD_LINK = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)")

# Phrases that hint at invented experience, guarantees, hype or false urgency.
SUSPECT_PHRASES = [
    (r"\bI (?:tried|tested|used|bought|took|followed)\b", "personal experience claim: only keep if it is true"),
    (r"\bin my experience\b", "personal experience claim: only keep if it is true"),
    (r"\bmy (?:clients|students|results)\b", "personal claim: only keep if it is true"),
    (r"\bguarantee[ds]?\b", "'guarantee' wording: keep only if it is the vendor's stated guarantee"),
    (r"\bresults? in \d+ (?:days?|weeks?|hours?)\b", "time-to-result claim"),
    (r"\b(?:limited time|act now|hurry|last chance|don't miss|only \d+ left)\b", "false urgency wording"),
    (r"\b(?:life[- ]changing|miracle|secret|overnight|effortless)\b", "hype wording"),
    (r"\bstudies show\b|\bresearch shows\b|\baccording to (?:a )?(?:study|studies)\b", "study claim: needs a named source"),
]
PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s?%")


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end]
    body = text[end + 4:]
    fm = {}
    for line in fm_text.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm, body


def line_of(body, pos):
    return body.count("\n", 0, pos) + 1


def lint_file(path, is_draft):
    errors, warnings = [], []
    text = path.read_text(encoding="utf-8")
    fm, body = split_front_matter(text)

    if not fm.get("title"):
        errors.append("front matter: missing title")
    if not is_draft and not fm.get("date") and not re.match(r"\d{4}-\d{2}-\d{2}-", path.name):
        errors.append("front matter: missing date (and none in filename)")
    if not is_draft and not fm.get("last_modified_at"):
        warnings.append("front matter: no last_modified_at (updated date will not show)")
    if "In three sentences" not in body:
        warnings.append("no 'In three sentences' summary box")
    if not re.search(r"not (?:for|to)|skip it|should skip", body, re.I):
        warnings.append("no 'who it is not for' guidance found")

    # Affiliate links must be marked and tagged.
    has_amazon = False
    for m in ANCHOR.finditer(body):
        tag = m.group(0)
        href_m = HREF.search(tag)
        if not href_m:
            continue
        href = href_m.group(1)
        rel_m = REL.search(tag)
        rel = rel_m.group(1).lower() if rel_m else ""
        ln = line_of(body, m.start())
        if AMAZON_HOST.match(href):
            has_amazon = True
            if f"tag={AMAZON_TAG}" not in href:
                errors.append(f"line {ln}: Amazon link without tag={AMAZON_TAG}")
            if "sponsored" not in rel:
                errors.append(f"line {ln}: Amazon link missing rel=\"sponsored\"")
        elif CLICKBANK_HOST.match(href):
            if f"tid={CLICKBANK_TID_PREFIX}" not in href:
                errors.append(f"line {ln}: ClickBank link without tid={CLICKBANK_TID_PREFIX}...")
            if "sponsored" not in rel:
                errors.append(f"line {ln}: ClickBank link missing rel=\"sponsored\"")

    # Markdown-style affiliate links cannot carry rel attributes.
    for m in MD_LINK.finditer(body):
        url = m.group(1)
        if AMAZON_HOST.match(url) or CLICKBANK_HOST.match(url):
            errors.append(f"line {line_of(body, m.start())}: affiliate link in Markdown form (cannot set rel=sponsored); use an <a> tag")

    if has_amazon and "As an Amazon Associate" not in body:
        errors.append("Amazon links present but the 'As an Amazon Associate I earn from qualifying purchases' statement is missing")

    # The post layout must show the disclosure banner before the content.
    layout = (ROOT / "_layouts" / "post.html").read_text(encoding="utf-8")
    banner_pos = layout.find("disclosure-banner")
    m_content = re.search(r"\{\{\s*content[\s|}]", layout)
    content_pos = m_content.start() if m_content else -1
    if banner_pos == -1 or content_pos == -1 or banner_pos > content_pos:
        errors.append("_layouts/post.html: disclosure banner is not placed before the post content")

    # Wording that hints at unverified or invented claims.
    for pattern, msg in SUSPECT_PHRASES:
        for m in re.finditer(pattern, body, re.I):
            warnings.append(f"line {line_of(body, m.start())}: '{m.group(0)}' - {msg}")
    for m in PERCENT.finditer(body):
        warnings.append(f"line {line_of(body, m.start())}: '{m.group(0)}' - percentage: needs a named source")

    return errors, warnings


def main():
    files = []
    for d in POST_DIRS:
        if d.exists():
            files += [(p, d.name == "_drafts") for p in sorted(d.glob("*.md"))]
    if not files:
        print("No posts found.")
        return 0

    total_errors = 0
    for path, is_draft in files:
        errors, warnings = lint_file(path, is_draft)
        total_errors += len(errors)
        status = "FAIL" if errors else "ok"
        kind = "draft" if is_draft else "post"
        print(f"[{status}] {kind}: {path.relative_to(ROOT)}")
        for e in errors:
            print(f"    ERROR   {e}")
        for w in warnings:
            print(f"    warning {w}")
    print(f"\n{total_errors} error(s) in {len(files)} file(s).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
