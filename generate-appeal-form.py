#!/usr/bin/env python3
"""Generate MetLife Pet Insurance Claim Appeal Form PDFs.

Overlays claim data onto the official blank MetLife appeal form PDF,
and optionally appends an appeal letter as additional pages.

Usage:
    python3 generate-appeal-form.py --fill data.json --letter appeal-claim-3342951.md
    python3 generate-appeal-form.py --fill data.json --letter letter.md -o out.pdf
"""

import argparse
import io
import json
import os
import sys

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter as LETTER_SIZE
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLANK_FORM = os.path.join(SCRIPT_DIR, "appeal-form-blank.pdf")

PAGE_W, PAGE_H = LETTER_SIZE
MARGIN = 1.0 * 72  # 1 inch

# --- Field coordinates (from the official blank form, page 2) ---
MEMBER_FIELDS_LEFT = {
    "policy_number":   (165, 571.4),
    "pet_parent_name": (165, 557.4),
    "address":         (120, 543.4),
    "city":            (95,  530.4),
}
MEMBER_FIELDS_RIGHT = {
    "state": (310, 529.6),
    "zip":   (95,  516.6),
    "phone": (235, 515.6),
    "pet_name": (120, 502.4),
}

CLAIM_TREATMENT_DATE_X = 390
CLAIM_TREATMENT_DATE_Y = 557.0
CLAIM_ROW_SPACING = 20
CLAIM_PET_NAME_X = 390
CLAIM_PET_NAME_Y = 517.0

STAMP_X = 380
STAMP_Y = 230


def create_overlay(data):
    """Create a transparent PDF overlay with the filled data."""
    d = data or {}
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER_SIZE)

    # Page 1: instructions cover page (no data needed)
    c.showPage()

    # Page 2: the actual form
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#000000"))

    for field, (x, y) in MEMBER_FIELDS_LEFT.items():
        value = d.get(field, "")
        if value:
            c.drawString(x, y, str(value))

    for field, (x, y) in MEMBER_FIELDS_RIGHT.items():
        value = d.get(field, "")
        if value:
            c.drawString(x, y, str(value))

    claims = d.get("claims", [])
    if claims:
        claim = claims[0]
        treat_date = claim.get("treatment_date", "")
        claim_num = claim.get("claim_number", "")
        claim_label = treat_date
        if claim_num:
            claim_label += f" (Claim #{claim_num})"
        c.drawString(CLAIM_TREATMENT_DATE_X, CLAIM_TREATMENT_DATE_Y, claim_label)

        if len(claims) > 1:
            c.setFillColor(HexColor("#FFFFFF"))
            c.rect(CLAIM_TREATMENT_DATE_X - 2, 535, 220, 14, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            y_offset = CLAIM_TREATMENT_DATE_Y - CLAIM_ROW_SPACING
            for extra_claim in claims[1:]:
                t = extra_claim.get("treatment_date", "")
                n = extra_claim.get("claim_number", "")
                label = t
                if n:
                    label += f" (Claim #{n})"
                c.setFont("Helvetica", 9)
                c.drawString(CLAIM_TREATMENT_DATE_X, y_offset, label)
                y_offset -= CLAIM_ROW_SPACING
            c.setFont("Helvetica", 10)

        pet_name = claim.get("claim_pet_name", "")
        c.drawString(CLAIM_PET_NAME_X, CLAIM_PET_NAME_Y, pet_name)

    vet_stamp = d.get("vet_clinic_stamp", "")
    if vet_stamp:
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#333333"))
        for line in vet_stamp.split("\n"):
            c.drawString(STAMP_X, STAMP_Y, line)
            STAMP_Y_local = STAMP_Y
        sy = STAMP_Y
        for line in vet_stamp.split("\n"):
            c.drawString(STAMP_X, sy, line)
            sy -= 11

    c.save()
    buf.seek(0)
    return buf


# Fix the vet stamp rendering (double-write bug above). Let me redo create_overlay cleanly:
def create_overlay(data):
    """Create a transparent PDF overlay with the filled data."""
    d = data or {}
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER_SIZE)

    # Page 1: instructions cover page (no data needed)
    c.showPage()

    # Page 2: the actual form
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#000000"))

    for field, (x, y) in MEMBER_FIELDS_LEFT.items():
        value = d.get(field, "")
        if value:
            c.drawString(x, y, str(value))

    for field, (x, y) in MEMBER_FIELDS_RIGHT.items():
        value = d.get(field, "")
        if value:
            c.drawString(x, y, str(value))

    claims = d.get("claims", [])
    if claims:
        claim = claims[0]
        treat_date = claim.get("treatment_date", "")
        claim_num = claim.get("claim_number", "")
        claim_label = treat_date
        if claim_num:
            claim_label += f" (Claim #{claim_num})"
        c.drawString(CLAIM_TREATMENT_DATE_X, CLAIM_TREATMENT_DATE_Y, claim_label)

        if len(claims) > 1:
            c.setFillColor(HexColor("#FFFFFF"))
            c.rect(CLAIM_TREATMENT_DATE_X - 2, 535, 220, 14, fill=1, stroke=0)
            c.setFillColor(HexColor("#000000"))
            y_offset = CLAIM_TREATMENT_DATE_Y - CLAIM_ROW_SPACING
            for extra_claim in claims[1:]:
                t = extra_claim.get("treatment_date", "")
                n = extra_claim.get("claim_number", "")
                label = t
                if n:
                    label += f" (Claim #{n})"
                c.setFont("Helvetica", 9)
                c.drawString(CLAIM_TREATMENT_DATE_X, y_offset, label)
                y_offset -= CLAIM_ROW_SPACING
            c.setFont("Helvetica", 10)

        pet_name = claim.get("claim_pet_name", "")
        c.drawString(CLAIM_PET_NAME_X, CLAIM_PET_NAME_Y, pet_name)

    vet_stamp = d.get("vet_clinic_stamp", "")
    if vet_stamp:
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#333333"))
        sy = STAMP_Y
        for line in vet_stamp.split("\n"):
            c.drawString(STAMP_X, sy, line)
            sy -= 11

    c.save()
    buf.seek(0)
    return buf


def render_letter_pages(letter_path):
    """Render a markdown appeal letter as PDF pages, return as BytesIO."""
    with open(letter_path) as f:
        text = f.read()

    paragraphs = text.strip().split("\n\n")
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER_SIZE)

    font_name = "Helvetica"
    font_size = 11
    line_h = 15
    text_w = PAGE_W - 2 * MARGIN

    y = PAGE_H - MARGIN

    def draw_line(text, x=MARGIN, bold=False):
        """Draw a single line, handling page breaks."""
        nonlocal y
        if y < MARGIN + 20:
            c.showPage()
            y = PAGE_H - MARGIN
        f = "Helvetica-Bold" if bold else font_name
        c.setFont(f, font_size)
        c.setFillColor(HexColor("#000000"))
        c.drawString(x, y, text)
        y -= line_h

    def wrap_and_draw(text, indent=0, bold=False):
        """Word-wrap text and draw each line."""
        f = "Helvetica-Bold" if bold else font_name
        wrapped = simpleSplit(text, f, font_size, text_w - indent)
        for i, wl in enumerate(wrapped):
            draw_line(wl, x=MARGIN + (indent if i > 0 else 0), bold=bold)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        lines_in_para = para.split("\n")

        # Detect numbered list items (e.g. "1. ...", "2. ...")
        is_numbered = all(
            line.strip().split(".")[0].isdigit()
            for line in lines_in_para if line.strip()
        )

        if is_numbered:
            for line in lines_in_para:
                line = line.strip()
                if not line:
                    continue
                wrap_and_draw(line, indent=15)
                y -= 2
        elif "\n" in para and not any(len(l) > 90 for l in lines_in_para):
            # Multi-line short blocks (address, Re: block, closing)
            for line in lines_in_para:
                line = line.strip()
                if not line:
                    continue
                is_bold = line.startswith("Re:")
                wrap_and_draw(line, bold=is_bold)
        else:
            # Regular paragraph — join lines and word wrap
            full = " ".join(l.strip() for l in lines_in_para)
            wrap_and_draw(full)

        y -= line_h * 0.4

    c.save()
    buf.seek(0)
    return buf


def main():
    parser = argparse.ArgumentParser(description="Generate MetLife appeal form PDF")
    parser.add_argument("--fill", required=True, help="JSON file with form data")
    parser.add_argument("--letter", help="Appeal letter markdown file to append")
    parser.add_argument("--output", "-o", default=None, help="Output PDF path")
    args = parser.parse_args()

    if not os.path.exists(BLANK_FORM):
        print(f"Error: Blank form not found at {BLANK_FORM}", file=sys.stderr)
        sys.exit(1)

    with open(args.fill) as f:
        data = json.load(f)

    output = args.output
    if not output:
        claims = data.get("claims", [])
        claim_num = claims[0].get("claim_number", "filled") if claims else "filled"
        output = f"appeal-form-{claim_num}.pdf"

    # Read the official blank form
    reader = PdfReader(BLANK_FORM)

    # Create the data overlay
    overlay_buf = create_overlay(data)
    overlay_reader = PdfReader(overlay_buf)

    # Merge overlay onto blank form
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])
        writer.add_page(page)

    # Append appeal letter pages if provided
    if args.letter and os.path.exists(args.letter):
        letter_buf = render_letter_pages(args.letter)
        letter_reader = PdfReader(letter_buf)
        for page in letter_reader.pages:
            writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
