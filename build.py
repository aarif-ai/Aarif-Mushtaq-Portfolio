"""Build the portfolio: render templates/ with content/*.yaml into dist/.

Usage:  python build.py

What it does, in order:
  1. Load every YAML file in content/ (the only source of site text).
  2. Render the Jinja2 templates into HTML pages in dist/.
  3. Copy static/ (CSS, JS, fonts, images, PDFs) into dist/.
  4. Check the rendered HTML against the content rules in CLAUDE.md §1.
     Any violation stops the build with a non-zero exit code.
  5. Print a short summary of pages built and file sizes vs the budget.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
import shutil
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"

# Phrases that must never appear on the site (CLAUDE.md §1).
# Each entry is (regular expression, human-readable reason). Matching ignores case.
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bevent assistant\b", "CampusHub AI Event Assistant must not be mentioned"),
    (r"\bvector database", "'vector database' is not allowed for CampusHub"),
    (r"\bsemantic search\b", "'semantic search' is not allowed for CampusHub"),
    (r"\blines of code\b", "lines-of-code counts are not allowed"),
    (r"\bpassionate\b", "buzzword"),
    (r"\binnovative\b", "buzzword"),
    (r"\bcutting[- ]edge\b", "buzzword"),
    (r"\bleverag(e|es|ed|ing)\b", "buzzword"),
    (r"\bsynerg(y|ies)\b", "buzzword"),
    (r"\bseamless(ly)?\b", "buzzword"),
    (r"\brobust\b", "buzzword"),
    (r"\bworld[- ]class\b", "buzzword"),
    (r"\bninja\b", "buzzword"),
    (r"\bguru\b", "buzzword"),
    (r"\brockstar\b", "buzzword"),
]

# "TODO" means "content not available yet" and must never reach the page.
TODO_PATTERN = re.compile(r"\bTODO\b")

# Phone numbers: an Indian-style 10-digit number (optionally with +91 and
# spaces/dashes), or a tel: link. Short numbers like 351 or 2025 never match.
PHONE_PATTERN = re.compile(
    r"tel:"
    r"|(?<![\w/.-])(?:\+\d{1,3}[\s-]?)?\d{5}[\s-]?\d{5}(?![\w/.-])"
    r"|(?<![\w/.-])\(?\d{3}\)?[\s-]\d{3}[\s-]\d{4}(?![\w/.-])"
)

# SHA-256 fingerprint of Aarif's private phone number (digits only). The
# number itself must never appear in this public repository, so only its
# fingerprint is stored: the build hashes every 10-digit run it finds in dist/
# and fails on a match (see has_private_number).
PRIVATE_NUMBER_SHA256 = "2d0865725b43dc9609270a4911f357072d90a814d3d588aee6a3e568d0a1575c"

# Files no page may ever link to, with the reason (checked in every href/src).
FORBIDDEN_FILES: dict[str, str] = {
    "Aarif_Mushtaq_Resume_v1.pdf": "the old resume PDF contains a phone number; "
                                   "link to /resume.html instead",
}

# Performance budget from CLAUDE.md §6, in kilobytes (uncompressed).
BUDGET_KB: dict[str, int] = {"CSS": 40, "JS": 30, "Fonts": 150}
FONT_SUFFIXES = {".woff2", ".woff", ".ttf", ".otf"}


# ---------------------------------------------------------------- content


def load_content() -> dict[str, Any]:
    """Load every content/*.yaml file into one dictionary.

    The key is the file name without ".yaml", so content/site.yaml becomes
    `site` in the templates, content/projects.yaml becomes `projects`, etc.
    """
    content: dict[str, Any] = {}
    for path in sorted(CONTENT_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as file:
            content[path.stem] = yaml.safe_load(file)
    if not content:
        raise SystemExit(f"Build failed: no YAML files found in {CONTENT_DIR}")
    return content


def image_size(path: Path) -> tuple[int, int]:
    """Read the pixel width and height of a .webp or .svg file.

    The sizes go into width/height attributes so the browser reserves the
    right space before the image loads (no layout shift).
    WebP: the size sits in the file header, in one of three formats
    (VP8 lossy, VP8L lossless, VP8X extended).
    SVG: the size comes from the viewBox="0 0 width height" attribute.
    """
    if path.suffix == ".svg":
        text = path.read_text(encoding="utf-8")
        match = re.search(r'viewBox="\s*[\d.-]+[\s,]+[\d.-]+[\s,]+([\d.]+)[\s,]+([\d.]+)', text)
        if not match:
            raise SystemExit(f"Build failed: {path.name} has no viewBox")
        return round(float(match.group(1))), round(float(match.group(2)))

    if path.suffix == ".webp":
        header = path.read_bytes()[:30]
        chunk = header[12:16]
        if chunk == b"VP8 ":
            width = int.from_bytes(header[26:28], "little") & 0x3FFF
            height = int.from_bytes(header[28:30], "little") & 0x3FFF
            return width, height
        if chunk == b"VP8L":
            bits = int.from_bytes(header[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":
            width = int.from_bytes(header[24:27], "little") + 1
            height = int.from_bytes(header[27:30], "little") + 1
            return width, height

    raise SystemExit(f"Build failed: can't read the size of {path.name} "
                     "(only .webp and .svg are supported)")


def load_svg(path: Path, alt: str) -> Markup:
    """Read a diagram SVG so it can be placed directly inside the page.

    Inline SVG (not <img>) is what lets the diagram use the site's colour
    tokens (light/dark theme) and the CSS draw-in animation. Because the
    file becomes part of the page, it is checked first:
      - no <script>, <style>, style="" or on...="" attributes (the Content
        Security Policy would block them, and they don't belong in a diagram)
      - its <title> must be exactly the `alt` text from the YAML, so the
        YAML stays the one source for what the diagram says.
    """
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*\?>\s*", "", text)   # drop the XML header line

    forbidden = re.search(r"<script|<style|\sstyle=|\son\w+=", text, re.IGNORECASE)
    if forbidden:
        raise SystemExit(f"Build failed: {path.name} contains "
                         f"'{forbidden.group(0).strip()}', which isn't allowed")

    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.DOTALL)
    if not title or title.group(1).strip() != str(escape(alt)):
        raise SystemExit(f"Build failed: the <title> of {path.name} must be "
                         f"exactly its alt text from the YAML:\n  {alt}")
    return Markup(text)


def add_file_flags(data: Any) -> None:
    """Mark every YAML entry that points at a file with whether it exists.

    Any dictionary with a `file` key (diagrams, figures) gets:
      exists: True/False  - is the file in static/ right now?
      width, height       - its size, only when it exists
      svg                 - for .svg files: the checked file content, to be
                            placed inline (see load_svg)
    Templates render the image only `if item.exists`, so a diagram or figure
    that hasn't been made yet simply doesn't appear (no broken image).
    """
    if isinstance(data, list):
        for value in data:
            add_file_flags(value)
    elif isinstance(data, dict):
        if isinstance(data.get("file"), str):
            path = STATIC_DIR / data["file"].lstrip("/")
            data["exists"] = path.is_file()
            if data["exists"]:
                data["width"], data["height"] = image_size(path)
                if path.suffix == ".svg":
                    data["svg"] = load_svg(path, data["alt"])
        for value in data.values():
            add_file_flags(value)


def add_page_flags(content: dict[str, Any]) -> None:
    """Mark each project with `has_page`: will its case-study page be built?

    Case-study pages come from templates/case_study.html. Without that
    template, project cards show the title as plain text instead of a link
    to a page that doesn't exist.

    Also checks that each slug is simple (a-z, 0-9, -) and that `page`
    matches the file the build writes, /<slug>.html, so a typo in the YAML
    fails the build instead of producing a broken link.
    """
    has_template = (TEMPLATES_DIR / "case_study.html").exists()
    for project in content["projects"]["items"]:
        slug = project["slug"]
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            raise SystemExit(f"Build failed: project slug '{slug}' may only "
                             "use a-z, 0-9 and -")
        if project["page"] != f"/{slug}.html":
            raise SystemExit(f"Build failed: project '{slug}' has page "
                             f"'{project['page']}', expected '/{slug}.html'")
        project["has_page"] = has_template


def italic(text: str) -> Markup:
    """Template filter: turn *text* into <em>text</em>. Nothing else.

    The text is HTML-escaped first, so YAML can never inject HTML; only the
    <em> tags this function adds are real markup.
    """
    escaped = str(escape(text))
    return Markup(re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", escaped))


# -------------------------------------------------------------- rendering


def make_environment() -> Environment:
    """Create the Jinja2 environment used for every page.

    - StrictUndefined: using a key that doesn't exist in the YAML raises an
      error instead of silently printing nothing.
    - autoescape: characters like < and & in the YAML are escaped, so text is
      always shown as text.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        undefined=StrictUndefined,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["italic"] = italic
    return env


def write_page(env: Environment, template_name: str, out_name: str,
               context: dict[str, Any]) -> Path:
    """Render one template with the given context and save it in dist/."""
    html = env.get_template(template_name).render(**context)
    out_path = DIST_DIR / out_name
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_pages(env: Environment, content: dict[str, Any]) -> list[Path]:
    """Render index.html, one page per project, resume.html and 404.html.

    Also renders css/view-transitions.css, which gives each project title a
    unique transition name (see that template). It is a stylesheet, not a
    page, so it isn't in the returned list of pages.

    Templates that haven't been written yet are skipped with a note, not an
    error. templates/og.html is never rendered here: it is only used by
    scripts/make_og.py to draw the social preview image.
    """
    pages = [write_page(env, "index.html", "index.html", content)]

    if (TEMPLATES_DIR / "case_study.html").exists():
        for project in content["projects"]["items"]:
            context = {**content, "project": project}
            pages.append(write_page(env, "case_study.html",
                                    f"{project['slug']}.html", context))
    else:
        print("  note: templates/case_study.html not created yet - skipped")

    if (TEMPLATES_DIR / "resume.html").exists():
        pages.append(write_page(env, "resume.html", "resume.html", content))

    if (TEMPLATES_DIR / "404.html").exists():
        pages.append(write_page(env, "404.html", "404.html", content))
    else:
        print("  note: templates/404.html not created yet - skipped")

    write_page(env, "view-transitions.css", "css/view-transitions.css", content)
    return pages


def check_site_url(content: dict[str, Any]) -> str:
    """Return site.url without a trailing slash; stop if it's missing or not https."""
    url = content["site"].get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise SystemExit("Build failed: site.url in content/site.yaml must be set "
                         "and start with https://")
    return url.rstrip("/")


def write_robots_and_sitemap(site_url: str, pages: list[Path], updated: str) -> None:
    """Write dist/robots.txt (allow all) and dist/sitemap.xml (every page but 404).

    `updated` is site.last_updated ("21 Nov 2026"); the sitemap wants it as
    an ISO date (2026-11-21) in <lastmod>.
    """
    (DIST_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n",
        encoding="utf-8", newline="\n")

    lastmod = datetime.strptime(updated, "%d %b %Y").date().isoformat()
    urls = []
    for page in pages:
        if page.name == "404.html":
            continue
        path = "/" if page.name == "index.html" else f"/{page.name}"
        urls.append(f"  <url>\n    <loc>{site_url}{path}</loc>\n"
                    f"    <lastmod>{lastmod}</lastmod>\n  </url>\n")
    (DIST_DIR / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(urls) + "</urlset>\n",
        encoding="utf-8", newline="\n")


def prepare_dist() -> None:
    """Delete the old dist/ folder and copy static/ into a fresh one."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    # Not copied: private originals (img/ and docs/), and diagrams, which
    # are placed inline in the pages instead (see load_svg).
    shutil.copytree(STATIC_DIR, DIST_DIR,
                    ignore=shutil.ignore_patterns("originals", "diagrams"))


# ----------------------------------------------------------------- checks


class LinkCollector(HTMLParser):
    """Collect every href/src value and every id attribute in one page."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        """Called by HTMLParser for each opening tag, e.g. <a href="...">."""
        for name, value in attrs:
            if name in ("href", "src") and value is not None:
                self.links.append(value)
            elif name == "id" and value:
                self.ids.add(value)


def check_text_rules(html: str) -> list[str]:
    """Return a message for every forbidden phrase, TODO or phone number."""
    problems: list[str] = []
    for pattern, reason in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            problems.append(f"forbidden phrase '{match.group(0)}' ({reason})")
    if TODO_PATTERN.search(html):
        problems.append("contains 'TODO' (content not ready must render nothing)")
    for match in PHONE_PATTERN.finditer(html):
        problems.append(f"looks like a phone number: '{match.group(0)}'")
    return problems


def check_local_links(page: Path, html: str) -> list[str]:
    """Return a message for every local link or src that doesn't exist.

    External links (https:, mailto:) are not checked. "#section" links must
    point to an id on the same page. An empty href is always an error, and
    so is any link to a file in FORBIDDEN_FILES.
    """
    collector = LinkCollector()
    collector.feed(html)
    problems: list[str] = []

    for link in collector.links:
        if link.strip() == "":
            problems.append("empty href/src")
            continue
        for name, reason in FORBIDDEN_FILES.items():
            if name in link:
                problems.append(f"links to '{name}' ({reason})")
        parts = urlsplit(link)
        if parts.scheme or parts.netloc:      # https://..., mailto:..., //cdn
            continue
        if not parts.path:                    # "#about" on the same page
            if parts.fragment and parts.fragment not in collector.ids:
                problems.append(f"anchor '{link}' has no matching id")
            continue

        path = unquote(parts.path)
        if path.startswith("/"):
            target = DIST_DIR / path.lstrip("/")
        else:
            target = page.parent / path
        if path.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            problems.append(f"broken local link '{link}'")
    return problems


def has_private_number(text: str) -> bool:
    """True if any 10 digits in a row in `text` are the private phone number.

    Digits may be separated by spaces or dashes ("91034 81919"). Each 10-digit
    window is hashed and compared with PRIVATE_NUMBER_SHA256.
    """
    for run in re.findall(r"\d(?:[\s-]?\d){9,}", text):
        digits = re.sub(r"\D", "", run)
        for start in range(len(digits) - 9):
            window = digits[start:start + 10].encode()
            if hashlib.sha256(window).hexdigest() == PRIVATE_NUMBER_SHA256:
                return True
    return False


def searchable_text(path: Path) -> str:
    """The text of any file in dist/, for the private-number check.

    Always includes the raw bytes. For PDFs, the page text and metadata are
    added via PyMuPDF when it is installed (requirements-dev.txt): PDF text
    is usually compressed, so raw bytes alone can miss it. Netlify doesn't
    install PyMuPDF, so there the raw-bytes search is used on its own.
    """
    text = path.read_bytes().decode("latin-1")
    if path.suffix.lower() == ".pdf":
        try:
            import pymupdf
        except ImportError:
            return text
        with pymupdf.open(path) as doc:
            text += str(doc.metadata) + (doc.get_xml_metadata() or "")
            text += "".join(page.get_text() for page in doc)
    return text


def check_dist_files() -> list[str]:
    """Fail on any file in dist/ (HTML, CSS, JS, PDF, images…) with the private number."""
    return [f"{path.relative_to(DIST_DIR).as_posix()}: contains the private phone number"
            for path in sorted(DIST_DIR.rglob("*"))
            if path.is_file() and has_private_number(searchable_text(path))]


def check_head_tags(html: str) -> list[str]:
    """Every page needs a <title>, a meta description (≤ 160 characters,
    so search results don't cut it off) and an og:image."""
    problems: list[str] = []
    if not re.search(r"<title>\s*\S[^<]*</title>", html):
        problems.append("missing or empty <title>")
    description = re.search(r'<meta name="description" content="([^"]+)"', html)
    if not description:
        problems.append("missing meta description")
    elif len(unescape(description.group(1))) > 160:
        problems.append(f"meta description is {len(unescape(description.group(1)))} "
                        "characters; keep it at 160 or fewer")
    if not re.search(r'<meta property="og:image" content="https://[^"]+"', html):
        problems.append("missing og:image (absolute https URL)")
    return problems


def check_og_image(content: dict[str, Any]) -> list[str]:
    """The social preview image must exist in dist/ and be 1200×630 pixels.

    PNG stores width and height as two 4-byte numbers at bytes 16–24.
    """
    path = DIST_DIR / content["site"]["seo"]["image"].lstrip("/")
    if not path.is_file():
        return [f"{path.relative_to(DIST_DIR).as_posix()} is missing "
                "(run: python scripts/make_og.py)"]
    header = path.read_bytes()[:24]
    size = (int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big"))
    if header[:8] != b"\x89PNG\r\n\x1a\n" or size != (1200, 630):
        return [f"{path.name} must be a 1200×630 PNG (got {size})"]
    return []


def check_pages(pages: list[Path]) -> list[str]:
    """Run every check on every page; return all problems with page names."""
    problems: list[str] = []
    for page in pages:
        html = page.read_text(encoding="utf-8")
        found = check_text_rules(html) + check_local_links(page, html) + check_head_tags(html)
        for problem in found:
            problems.append(f"{page.name}: {problem}")
    return problems


# ---------------------------------------------------------------- summary


def size_kb(paths: list[Path]) -> float:
    """Total size of the given files in kilobytes."""
    return sum(path.stat().st_size for path in paths) / 1024


def print_summary(pages: list[Path]) -> None:
    """Print pages built and HTML/CSS/JS/font sizes vs the §6 budget."""
    files = [path for path in DIST_DIR.rglob("*") if path.is_file()]
    groups = {
        "HTML": [p for p in files if p.suffix == ".html"],
        "CSS": [p for p in files if p.suffix == ".css"],
        "JS": [p for p in files if p.suffix == ".js"],
        "Fonts": [p for p in files if p.suffix in FONT_SUFFIXES],
    }

    print(f"\nPages built ({len(pages)}): " + ", ".join(p.name for p in pages))
    print("Sizes (uncompressed):")
    for name, group in groups.items():
        total = size_kb(group)
        line = f"  {name:<6}{total:8.1f} KB"
        if name in BUDGET_KB:
            limit = BUDGET_KB[name]
            status = "ok" if total <= limit else "OVER BUDGET"
            line += f"  / {limit} KB  {status}"
        print(line)


# ------------------------------------------------------------------- main


def main() -> int:
    """Run the whole build. Returns 0 on success, 1 on any failure."""
    print("Building portfolio...")
    try:
        content = load_content()
        site_url = check_site_url(content)
        add_file_flags(content)
        add_page_flags(content)
        prepare_dist()
        pages = render_pages(make_environment(), content)
        write_robots_and_sitemap(site_url, pages, content["site"]["last_updated"])
    except yaml.YAMLError as error:
        print(f"\nBuild FAILED: a YAML file in content/ is invalid:\n{error}")
        return 1
    except TemplateError as error:
        # StrictUndefined errors land here, e.g. "'dict object' has no
        # attribute 'heroo'" when a template uses a key the YAML lacks.
        print(f"\nBuild FAILED: template error: {error}")
        return 1

    problems = check_pages(pages) + check_og_image(content) + check_dist_files()
    if problems:
        print(f"\nBuild FAILED: {len(problems)} rule violation(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print_summary(pages)
    print("\nBuild OK -> dist/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
