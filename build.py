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

import re
import shutil
import sys
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


def add_file_flags(data: Any) -> None:
    """Mark every YAML entry that points at a file with whether it exists.

    Any dictionary with a `file` key (diagrams, figures) gets:
      exists: True/False  - is the file in static/ right now?
      width, height       - its size, only when it exists
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
        for value in data.values():
            add_file_flags(value)


def add_page_flags(content: dict[str, Any]) -> None:
    """Mark each project with `has_page`: will its case-study page be built?

    Case-study pages come from templates/case_study.html (Step 7). Until that
    template exists, project cards show the title as plain text instead of a
    link to a page that doesn't exist yet.
    """
    has_template = (TEMPLATES_DIR / "case_study.html").exists()
    for project in content["projects"]["items"]:
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
    """Render index.html, one page per project, and 404.html.

    Templates that haven't been written yet (case_study.html and 404.html
    arrive in later build steps) are skipped with a note, not an error.
    """
    pages = [write_page(env, "index.html", "index.html", content)]

    if (TEMPLATES_DIR / "case_study.html").exists():
        for project in content["projects"]["items"]:
            context = {**content, "project": project}
            pages.append(write_page(env, "case_study.html",
                                    f"{project['slug']}.html", context))
    else:
        print("  note: templates/case_study.html not created yet - skipped")

    if (TEMPLATES_DIR / "404.html").exists():
        pages.append(write_page(env, "404.html", "404.html", content))
    else:
        print("  note: templates/404.html not created yet - skipped")

    return pages


def prepare_dist() -> None:
    """Delete the old dist/ folder and copy static/ into a fresh one."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    shutil.copytree(STATIC_DIR, DIST_DIR,
                    ignore=shutil.ignore_patterns("originals"))


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
    point to an id on the same page. An empty href is always an error.
    """
    collector = LinkCollector()
    collector.feed(html)
    problems: list[str] = []

    for link in collector.links:
        if link.strip() == "":
            problems.append("empty href/src")
            continue
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


def check_pages(pages: list[Path]) -> list[str]:
    """Run every check on every page; return all problems with page names."""
    problems: list[str] = []
    for page in pages:
        html = page.read_text(encoding="utf-8")
        for problem in check_text_rules(html) + check_local_links(page, html):
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
        add_file_flags(content)
        add_page_flags(content)
        prepare_dist()
        pages = render_pages(make_environment(), content)
    except yaml.YAMLError as error:
        print(f"\nBuild FAILED: a YAML file in content/ is invalid:\n{error}")
        return 1
    except TemplateError as error:
        # StrictUndefined errors land here, e.g. "'dict object' has no
        # attribute 'heroo'" when a template uses a key the YAML lacks.
        print(f"\nBuild FAILED: template error: {error}")
        return 1

    problems = check_pages(pages)
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
