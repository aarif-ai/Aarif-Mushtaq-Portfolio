"""Draw the social preview image (static/img/og.png, 1200×630).

Usage (from the project folder, with the venv active):
    pip install -r requirements-dev.txt          # once: installs Pillow
    python scripts/make_og.py

Needs Google Chrome, Chromium or Microsoft Edge installed. If it isn't
found, set CHROME to its full path, e.g.:
    set CHROME=C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe

How it works:
  1. Render templates/og.html with the site's YAML (name, eyebrow,
     availability) into a temporary folder. The template is dev-only:
     build.py never publishes it.
  2. Take a 1200×630 screenshot of it with headless Chrome.
  3. Save it as PNG with Pillow; if it is over 200 KB, reduce it to 256
     colours (with dithering) to keep link previews fast.

Rerun it whenever the name, eyebrow, availability or photo changes.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (reuse the site's YAML loading and Jinja settings)

OUTPUT = ROOT / "static" / "img" / "og.png"
SIZE = (1200, 630)
MAX_BYTES = 200 * 1024

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome() -> str:
    """Return the path of a Chrome-like browser, or stop with a clear message."""
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("make_og: Chrome/Chromium/Edge not found; set CHROME to its path")


def render_html(folder: Path) -> Path:
    """Write templates/og.html, filled in from the YAML, into `folder`."""
    content = build.load_content()
    html = build.make_environment().get_template("og.html").render(
        **content, root=ROOT.as_uri())
    path = folder / "og.html"
    path.write_text(html, encoding="utf-8")
    return path


def screenshot(chrome: str, page: Path, folder: Path) -> Path:
    """Photograph the page at exactly 1200×630 with headless Chrome."""
    shot = folder / "shot.png"
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", f"--window-size={SIZE[0]},{SIZE[1]}",
        f"--user-data-dir={folder / 'profile'}", "--allow-file-access-from-files",
        "--virtual-time-budget=3000", f"--screenshot={shot}", page.as_uri(),
    ], check=True, capture_output=True, timeout=120)
    if not shot.is_file():
        sys.exit("make_og: Chrome didn't produce a screenshot")
    return shot


def save_small_png(shot: Path) -> None:
    """Save the screenshot as OUTPUT, 1200×630 and under MAX_BYTES if possible."""
    image = Image.open(shot).convert("RGB")
    if image.size != SIZE:
        image = image.crop((0, 0, *SIZE))
    image.save(OUTPUT, optimize=True)
    if OUTPUT.stat().st_size > MAX_BYTES:
        image.quantize(colors=256, dither=Image.Dither.FLOYDSTEINBERG).save(OUTPUT, optimize=True)
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"wrote {OUTPUT.relative_to(ROOT).as_posix()}  {SIZE[0]}×{SIZE[1]}  {size_kb:.0f} KB")
    if OUTPUT.stat().st_size > MAX_BYTES:
        sys.exit(f"make_og: still over {MAX_BYTES // 1024} KB")


def main() -> None:
    """Render, photograph and save the social preview image."""
    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        save_small_png(screenshot(chrome, render_html(folder), folder))


if __name__ == "__main__":
    main()
