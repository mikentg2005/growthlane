"""Build _data/book_lists.json for the /links/ page (the Instagram "link in bio" book list).

Run from the repo root after adding or editing an article:
    python pipeline/make_links_data.py

Reads every post in _posts/: the title, date, kind of article and the books
(asin, title, author) taken from the numbered "## 1. Title, Author" headings that
sit above each {% include book-cover.html %}. Single-book reviews have no such
include, so they are listed in SINGLE below.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "_posts"
BOOKS = ROOT / "assets" / "books"
OUT = ROOT / "_data" / "book_lists.json"

# slug -> (book title, author, asin, topic) for reviews of one book
SINGLE = {
    "flip-thinking-berthold-gunster-review": ("Flip Thinking", "Berthold Gunster", "1529146283", "Mindset"),
}

INCLUDE = re.compile(r'\{%\s*include book-cover\.html asin="(\w+)" title="([^"]+)"\s*%\}')
HEADING = re.compile(r"^##\s+\d+\.\s+(.*)$")


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    data = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        data[k.strip()] = v.strip().strip('"')
    return data


def short_author(author):
    """Keep long author lists readable: 'First Author and co-authors'."""
    names = [n.strip() for n in re.split(r",| and ", author) if n.strip()]
    return author if len(names) <= 3 else f"{names[0]} and co-authors"


def books_from(text):
    books, heading = [], ""
    for line in text.splitlines():
        h = HEADING.match(line)
        if h:
            heading = h.group(1).strip()
        m = INCLUDE.search(line)
        if m:
            asin, title = m.group(1), m.group(2)
            author = heading[len(title):].lstrip(", ") if heading.startswith(title) else ""
            books.append({"asin": asin, "title": title, "author": author})
    return books


def topic_of(title):
    """'5 Best Books on Leadership for New Managers' -> 'Leadership'."""
    m = re.match(r"^\d+ Best Books on (.*?)(?: for .*)?$", title)
    return m.group(1) if m else title


def main():
    lists = []
    seen = set()  # a book that is in two articles is listed once, under the newest one
    for path in sorted(POSTS.glob("*.md"), reverse=True):
        y, mo, d, slug = re.match(r"(\d{4})-(\d{2})-(\d{2})-(.*)\.md$", path.name).groups()
        text = path.read_text(encoding="utf-8")
        fm = front_matter(text)
        books = books_from(text)
        if not books and slug in SINGLE:
            title, author, asin, _ = SINGLE[slug]
            books = [{"asin": asin, "title": title, "author": author}]
        books = [b for b in books if b["asin"] not in seen]
        seen.update(b["asin"] for b in books)
        for b in books:
            b["cover"] = (BOOKS / f"{b['asin']}.jpg").exists()
            b["author"] = short_author(b["author"])
        article = re.sub(r"\s*\(.*\)$", "", fm["title"])
        lists.append({
            "topic": SINGLE[slug][3] if slug in SINGLE else topic_of(article),
            "title": article,
            "url": f"/{y}/{mo}/{d}/{slug}/",
            "category": fm.get("category", ""),
            "basis": fm.get("basis", ""),
            "books": books,
        })
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(lists, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT, f"({len(lists)} articles, {sum(len(l['books']) for l in lists)} books)")


if __name__ == "__main__":
    main()
