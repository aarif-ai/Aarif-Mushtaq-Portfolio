"""Make the public copy of the resume PDF, without the phone number.

Usage (from the project folder, with the venv active):
    pip install -r requirements-dev.txt          # once: installs PyMuPDF
    python scripts/make_public_resume.py
    python scripts/make_public_resume.py --preview compare.png   # optional

Input : static/docs/originals/Aarif_Mushtaq_Resume_v1.pdf   (git-ignored, private)
Output: static/docs/Aarif_Mushtaq_Resume.pdf                 (public, linked from the site)

Rerun it whenever the resume changes. If the contact line's layout changes a
lot, the script stops with a clear message instead of writing a broken file.

The phone number itself is never written in this file (the repository is
public): it is found in the private original at run time.

How it works:
  1. Find the contact line ("Kashmir, India · +91 … · email · LinkedIn · GitHub")
     and measure how wide the phone part is (W).
  2. Redact the whole contact line: its text and the link underlines are
     really deleted from the file, not just covered.
  3. Redraw the line from the original PDF drawing commands, minus the phone
     bytes, at its original place in the drawing order (so text tools and
     ATS parsers still read it right after the name). This reuses the exact
     embedded font, size and colours. (The embedded font is a subset with its
     own private character codes, so drawing it as new Unicode text would
     print the wrong letters.) The line was centred, so it starts W/2 further
     right; everything after the removed part (email, LinkedIn, GitHub,
     underlines, link areas) moves W/2 left. Nothing else on the page moves.
  4. Check the result: 1 page, the expected contact text, all other text and
     pixels unchanged, links present, no phone number anywhere.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "static" / "docs" / "originals" / "Aarif_Mushtaq_Resume_v1.pdf"
OUTPUT = ROOT / "static" / "docs" / "Aarif_Mushtaq_Resume.pdf"

# The phone part as shown on the page: "+91", 10 digits, then " · ".
PHONE_PATTERN = re.compile(r"\+91 (\d{10}) · ")
EXPECTED_LINE = "Kashmir, India · aarifmushtaq542@gmail.com · LinkedIn · github.com/aarif-ai"
EXPECTED_LINKS = (
    "mailto:aarifmushtaq542@gmail.com",
    "https://www.linkedin.com/in/aarif-mushtaq-167708398",
    "https://github.com/aarif-ai",
)


def fail(message: str) -> None:
    """Stop with a clear message and a non-zero exit code."""
    sys.exit(f"make_public_resume: {message}")


def in_stream(shown: str) -> bytes:
    """How shown text is written in the PDF's drawing commands.

    The embedded subset font stores "·" as byte 1, written as \\001.
    """
    return shown.replace("·", "\\001").encode("latin-1")


def find_contact_line(page: pymupdf.Page) -> tuple[pymupdf.Rect, str, float]:
    """Return the contact line's rectangle, the phone part's text, and its width W.

    W is measured from the character boxes: from the "+" of the phone number
    to the first character after the separator that follows it.
    """
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [c for span in line["spans"] for c in span["chars"]]
            text = "".join(c["c"] for c in chars)
            match = PHONE_PATTERN.search(text)
            if match:
                width = chars[match.end()]["bbox"][0] - chars[match.start()]["bbox"][0]
                return pymupdf.Rect(line["bbox"]), match.group(0), width
    fail("couldn't find a '+91 … · ' phone part on page 1")
    raise AssertionError  # unreachable, keeps type checkers happy


def find_line_commands(content: bytes, phone: str) -> bytes:
    """Return the original drawing commands (q … Q) of the contact line."""
    match = re.search(rb"q\n1 0 0 1 [\d.]+ [\d.]+ cm\nq\n[^Q]*?"
                      + re.escape(in_stream(phone)) + rb".*?ET\nQ\nQ",
                      content, re.DOTALL)
    if not match:
        fail("couldn't find the contact line's drawing commands; "
             "the resume layout has changed, update this script")
    return match.group(0)


def rewrite_commands(commands: bytes, phone: str, shift: float) -> bytes:
    """Remove the phone bytes and move the line so it stays centred.

    - The text start (the "Td" offset) moves right by `shift` (= W/2).
    - The underlines, which all sit after the phone number, move left by
      `shift`, together with the text they underline.
    """
    new = commands.replace(in_stream(phone), b"")

    td = re.search(rb"Tm (-?[\d.]+) 0 Td", new)
    if not td:
        fail("couldn't find the text start (Td) of the contact line")
    old_x = td.group(1).decode()
    new_x = float(old_x) + shift
    new = new.replace(f"Tm {old_x} 0 Td".encode(), f"Tm {new_x:.4f} 0 Td".encode())
    new = new.replace(f"T* -{old_x} 0 Td".encode(), f"T* -{new_x:.4f} 0 Td".encode())

    def move_underline(m: re.Match[bytes]) -> bytes:
        x1, y, x2 = float(m.group(1)), m.group(2).decode(), float(m.group(3))
        return f"n {x1 - shift:.4f} {y} m {x2 - shift:.4f} {y} l S".encode()

    return re.sub(rb"n ([\d.]+) ([\d.]+) m ([\d.]+) \2 l S", move_underline, new)


def make_public_copy() -> str:
    """Create OUTPUT from SOURCE (steps 1–3). Returns the removed phone part."""
    if not SOURCE.exists():
        fail(f"missing {SOURCE.relative_to(ROOT)}")
    doc = pymupdf.open(SOURCE)
    page = doc[0]

    line_rect, phone, phone_width = find_contact_line(page)
    shift = phone_width / 2
    commands = find_line_commands(page.read_contents(), phone)

    # Keep the contact line's links, to put them back after the redaction.
    # (Link areas reach a little above the text, so this zone is taller.)
    zone = pymupdf.Rect(line_rect.x0 - 2, line_rect.y0 - 3, line_rect.x1 + 2, line_rect.y1 + 1)
    links = [link for link in page.get_links() if pymupdf.Rect(link["from"]).intersects(zone)]

    # 2. Redact the whole line: text and underlines are deleted from the file.
    # The redaction box starts 1.5pt inside the line's top edge: the large name
    # sits just above, and any overlap would delete the name too.
    redact = pymupdf.Rect(line_rect.x0 - 1, line_rect.y0 + 1.5, line_rect.x1 + 1, line_rect.y1)
    page.add_redact_annot(redact)
    page.apply_redactions(
        images=pymupdf.PDF_REDACT_IMAGE_NONE,
        graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
        text=pymupdf.PDF_REDACT_TEXT_REMOVE,
    )
    page = doc.reload_page(page)           # refresh PyMuPDF's view after redacting
    for link in list(page.get_links()):
        if pymupdf.Rect(link["from"]).intersects(zone):
            page.delete_link(link)

    # 3. Redraw the line at its ORIGINAL place in the drawing order.
    page.clean_contents()                  # one content stream to edit
    xref = page.get_contents()[0]
    content = doc.xref_stream(xref)
    # The emptied contact block is still there ("q 1 0 0 1 x y cm …"); cleaning
    # changed its line breaks to spaces, so match any whitespace.
    cm_tokens = commands.split(b"\n")[1].split()
    anchor = re.search(rb"q\s+" + rb"\s+".join(map(re.escape, cm_tokens)), content)
    if not anchor:
        fail("couldn't find where the contact line was drawn")
    redrawn = rewrite_commands(commands, phone, shift)
    content = content[:anchor.start()] + redrawn + b"\n" + content[anchor.start():]
    doc.update_stream(xref, content)

    for link in links:
        rect = pymupdf.Rect(link["from"])
        link["from"] = pymupdf.Rect(rect.x0 - shift, rect.y0, rect.x1 - shift, rect.y1)
        page.insert_link(link)

    doc.save(OUTPUT, garbage=4, deflate=True)
    print(f"wrote {OUTPUT.relative_to(ROOT)}  (removed a {phone_width:.2f} pt wide phone part)")
    return phone


def verify(phone: str) -> None:
    """Step 4: check the public copy; stop with a message if anything is wrong."""
    doc = pymupdf.open(OUTPUT)
    original = pymupdf.open(SOURCE)
    digits = PHONE_PATTERN.match(phone).group(1)

    if doc.page_count != 1:
        fail(f"expected 1 page, got {doc.page_count}")
    text = doc[0].get_text()
    if EXPECTED_LINE not in text:
        fail(f"contact line should read:\n  {EXPECTED_LINE}")

    # All other text, in the same reading order, must be exactly the original's.
    if text != original[0].get_text().replace(phone, ""):
        fail("text other than the phone number changed")

    # Everything above and below the contact line must look identical.
    line_rect, _, _ = find_contact_line(original[0])
    for clip in (pymupdf.Rect(0, 0, 595.28, line_rect.y0 - 0.5),
                 pymupdf.Rect(0, line_rect.y1 + 0.5, 595.28, 841.89)):
        before = original[0].get_pixmap(dpi=100, clip=clip).samples
        after = doc[0].get_pixmap(dpi=100, clip=clip).samples
        if before != after:
            fail(f"the page changed outside the contact line (area {clip})")

    everything = text + str(doc.metadata) + (doc.get_xml_metadata() or "")
    if digits in everything or "+91" in everything:
        fail("the phone number is still in the file's text or metadata")
    if digits.encode() in OUTPUT.read_bytes():
        fail("the phone number is still in the file's raw bytes")

    uris = [link.get("uri") for link in doc[0].get_links()]
    for uri in EXPECTED_LINKS:
        if uri not in uris:
            fail(f"link missing: {uri}")
    print("verified: 1 page, contact line correct, rest of page unchanged, "
          "links present, no phone number")


def save_preview(path: Path) -> None:
    """Save a PNG: top third of the original (left) next to the public copy (right)."""
    top_third = pymupdf.Rect(0, 0, 595.28, 841.89 / 3)
    sheet = pymupdf.open()
    page = sheet.new_page(width=top_third.width * 2 + 20, height=top_third.height)
    page.show_pdf_page(pymupdf.Rect(0, 0, top_third.width, top_third.height),
                       pymupdf.open(SOURCE), 0, clip=top_third)
    page.show_pdf_page(pymupdf.Rect(top_third.width + 20, 0, top_third.width * 2 + 20, top_third.height),
                       pymupdf.open(OUTPUT), 0, clip=top_third)
    page.get_pixmap(dpi=150).save(path)
    print(f"preview saved to {path}")


def main() -> None:
    """Make, verify and optionally preview the public resume."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preview", type=Path, help="save a before/after PNG here")
    args = parser.parse_args()
    verify(make_public_copy())
    if args.preview:
        save_preview(args.preview)


if __name__ == "__main__":
    main()
