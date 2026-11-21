"""Make the small images of Aarif's photo: header avatar and favicons.

Usage (from the project folder, with the venv active):
    pip install -r requirements-dev.txt          # once: installs Pillow
    python scripts/make_icons.py
    python scripts/make_icons.py --preview zoom.png   # optional: 32px favicon, 8× zoom

Input : static/img/originals/aarif-original.jpg   (git-ignored)
Output:
    static/img/aarif-64.webp      header avatar, 64×64 (shown at 32px, sharp on 2× screens)
    static/favicon-32.png         browser tab icon, round, transparent corners
    static/favicon-16.png         small tab icon, round, transparent corners
    static/favicon.ico            the 16px and 32px icons in one file (classic /favicon.ico)
    static/apple-touch-icon.png   180×180, square, no transparency (iOS rounds it itself)

Rerun it whenever the photo changes. If the new photo is framed differently,
adjust FACE_CENTER and FACE_SIZE: at 16–32px a whole head-and-shoulders
picture is too small to recognise, so the icons use a tight crop of the face.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "static" / "img" / "originals" / "aarif-original.jpg"

# Square crop around the face, in pixels of the original photo (1932×2576).
FACE_CENTER = (880, 735)
FACE_SIZE = 880

# Supersampling for the round mask: draw the circle 4× larger, then shrink,
# so its edge is smooth (anti-aliased) instead of jagged.
MASK_SCALE = 4


def face_crop() -> Image.Image:
    """Open the original (respecting its camera rotation) and crop the face square."""
    photo = ImageOps.exif_transpose(Image.open(SOURCE)).convert("RGB")
    x, y = FACE_CENTER
    half = FACE_SIZE // 2
    return photo.crop((x - half, y - half, x + half, y + half))


def resized(image: Image.Image, size: int) -> Image.Image:
    """High-quality square resize."""
    return image.resize((size, size), Image.Resampling.LANCZOS)


def round_icon(image: Image.Image, size: int) -> Image.Image:
    """The image as a circle on a transparent background, `size`×`size`."""
    big = size * MASK_SCALE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    icon = resized(image, size).convert("RGBA")
    icon.putalpha(mask.resize((size, size), Image.Resampling.LANCZOS))
    return icon


def save(image: Image.Image, path: Path, **options: object) -> None:
    """Save and print the file size, so it's easy to keep each file small."""
    image.save(path, **options)
    print(f"  {path.relative_to(ROOT).as_posix():32} {path.stat().st_size / 1024:5.1f} KB")


def main() -> None:
    """Write the avatar and the three favicons."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", type=Path, help="save the 32px favicon zoomed 8× here")
    args = parser.parse_args()

    face = face_crop()
    print("Wrote:")
    save(resized(face, 64), ROOT / "static" / "img" / "aarif-64.webp", quality=82, method=6)
    favicon_32 = round_icon(face, 32)
    favicon_16 = round_icon(face, 16)
    save(favicon_32, ROOT / "static" / "favicon-32.png", optimize=True)
    save(favicon_16, ROOT / "static" / "favicon-16.png", optimize=True)
    # One .ico holding both sizes, for browsers and tools that ask for
    # /favicon.ico directly. append_images supplies the exact 16px drawing
    # instead of letting Pillow shrink the 32px one.
    save(favicon_32, ROOT / "static" / "favicon.ico",
         format="ICO", sizes=[(16, 16), (32, 32)], append_images=[favicon_16])
    # 180×180 photo as PNG: reduced to 256 colours, which keeps it small
    # without visible banding at this size.
    apple = resized(face, 180).quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    save(apple, ROOT / "static" / "apple-touch-icon.png", optimize=True)

    if args.preview:
        zoom = Image.new("RGBA", (32 * 8, 32 * 8), (255, 255, 255, 255))
        zoom.alpha_composite(favicon_32.resize((32 * 8, 32 * 8), Image.Resampling.NEAREST))
        zoom.save(args.preview)
        print(f"preview saved to {args.preview}")


if __name__ == "__main__":
    main()
