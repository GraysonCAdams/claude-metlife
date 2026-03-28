#!/usr/bin/env python3
"""Generate MetLife Pet Insurance Claim Appeal Form PDFs.

Usage:
    python3 generate-appeal-form.py                  # blank template
    python3 generate-appeal-form.py --fill data.json  # filled from JSON
"""

import argparse
import json
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
BLUE = HexColor("#0072C6")
DARK = HexColor("#333333")
LIGHT_GRAY = HexColor("#F5F5F5")


def draw_form(c, data=None):
    """Draw the MetLife Claim Appeal Form on the canvas."""
    d = data or {}
    y = PAGE_H - MARGIN

    # Header bar
    c.setFillColor(BLUE)
    c.rect(0, y - 10, PAGE_W, 50, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, y + 5, "Claim Appeal Form")
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, y - 8, "MetLife Pet Insurance")

    y -= 50

    # Section 1: Member Info
    y -= 20
    c.setFillColor(BLUE)
    c.roundRect(MARGIN - 5, y - 5, 25, 25, 5, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 2, y, "1")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 30, y, "Member Info")

    y -= 30
    fields_left = [
        ("Policy Number:", d.get("policy_number", "")),
        ("Pet Parent Name:", d.get("pet_parent_name", "")),
        ("Address:", d.get("address", "")),
        ("City:", d.get("city", "")),
    ]
    fields_right = [
        ("State:", d.get("state", "")),
        ("Zip:", d.get("zip", "")),
        ("Phone:", d.get("phone", "")),
        ("Pet Name:", d.get("pet_name", "")),
    ]

    c.setFont("Helvetica", 10)
    start_y = y
    for label, value in fields_left:
        c.setFillColor(DARK)
        c.drawString(MARGIN, y, label)
        c.setFillColor(HexColor("#000000"))
        c.drawString(MARGIN + 100, y, value)
        # underline
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.line(MARGIN + 100, y - 3, MARGIN + 280, y - 3)
        y -= 22

    y = start_y
    x_right = PAGE_W / 2 + 20
    for label, value in fields_right:
        c.setFillColor(DARK)
        c.drawString(x_right, y, label)
        c.setFillColor(HexColor("#000000"))
        c.drawString(x_right + 80, y, value)
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.line(x_right + 80, y - 3, x_right + 240, y - 3)
        y -= 22

    y -= 15

    # Section 2: Claim to be Reviewed
    c.setFillColor(BLUE)
    c.roundRect(MARGIN - 5, y - 5, 25, 25, 5, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 2, y, "2")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 30, y, "Claim to be Reviewed")

    y -= 30
    claims = d.get("claims", [{"treatment_date": "", "claim_number": "", "claim_pet_name": ""}])
    c.setFont("Helvetica", 10)
    for claim in claims:
        c.setFillColor(DARK)
        c.drawString(MARGIN, y, "Treatment Date on Original Claim:")
        c.setFillColor(HexColor("#000000"))
        c.drawString(MARGIN + 195, y, claim.get("treatment_date", ""))
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.line(MARGIN + 195, y - 3, MARGIN + 340, y - 3)

        c.setFillColor(DARK)
        c.drawString(PAGE_W / 2 + 20, y, "Claim #:")
        c.setFillColor(HexColor("#000000"))
        c.drawString(PAGE_W / 2 + 70, y, claim.get("claim_number", ""))
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.line(PAGE_W / 2 + 70, y - 3, PAGE_W - MARGIN, y - 3)
        y -= 18

        c.setFillColor(DARK)
        c.drawString(MARGIN, y, "Pet Name:")
        c.setFillColor(HexColor("#000000"))
        c.drawString(MARGIN + 65, y, claim.get("claim_pet_name", ""))
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.line(MARGIN + 65, y - 3, MARGIN + 250, y - 3)
        y -= 25

    y -= 10

    # Section 3: Supporting Documentation
    c.setFillColor(BLUE)
    c.roundRect(MARGIN - 5, y - 5, 25, 25, 5, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 2, y, "3")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 30, y, "Supporting Documentation")

    y -= 25
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK)
    c.drawString(MARGIN, y, "Please attach any additional documentation necessary to re-evaluate your denied claim such as:")
    y -= 18
    bullets = [
        "Clarification of diagnosis (along with new diagnosis if applicable) within your Pet's legal medical records",
        "Clarification of symptoms / circumstances related to the claimed incident within your Pet's legal medical records",
        "Additional / Amended legal medical records",
    ]
    for bullet in bullets:
        c.drawString(MARGIN + 15, y, "\u2022  " + bullet)
        y -= 15

    y -= 15

    # Section 4: Sign and Date
    c.setFillColor(BLUE)
    c.roundRect(MARGIN - 5, y - 5, 25, 25, 5, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 2, y, "4")
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 30, y, "Sign and Date")

    y -= 22
    c.setFont("Helvetica", 8)
    c.setFillColor(DARK)
    declaration = (
        "Policyholder declaration: I declare my veterinarian recommended the treatment for which I am claiming. "
        "The particulars given are correct to the best of my knowledge and belief. I authorize my veterinarian to "
        "release medical records and give consent to MetLife Pet Insurance, to communicate with my veterinarian "
        "or veterinarian's staff."
    )
    # Word wrap the declaration
    from reportlab.lib.utils import simpleSplit
    lines = simpleSplit(declaration, "Helvetica", 8, PAGE_W - 2 * MARGIN)
    for line in lines:
        c.drawString(MARGIN, y, line)
        y -= 12

    y -= 10
    c.setFont("Helvetica", 10)

    # Signature lines
    sig_fields = [
        ("Pet Parent Signature", MARGIN, d.get("pet_parent_sig_date", "")),
        ("Treating Veterinarian Signature", MARGIN, d.get("vet_sig_date", "")),
    ]
    for label, x, date_val in sig_fields:
        c.setStrokeColor(HexColor("#000000"))
        c.line(x, y, x + 250, y)
        c.line(x + 280, y, x + 380, y)
        c.setFont("Helvetica", 8)
        c.setFillColor(DARK)
        c.drawString(x, y - 12, label)
        c.drawString(x + 280, y - 12, "Date")
        if date_val:
            c.setFont("Helvetica", 10)
            c.drawString(x + 285, y + 3, date_val)
        y -= 35

    # Vet clinic stamp area
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setDash(3, 3)
    vet_stamp = d.get("vet_clinic_stamp", "")
    stamp_x = PAGE_W / 2 + 40
    stamp_y = y + 70
    c.rect(stamp_x, stamp_y - 50, 200, 60, fill=0, stroke=1)
    c.setDash()
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#999999"))
    c.drawString(stamp_x + 5, stamp_y + 5, "Veterinary Clinic Stamp")
    if vet_stamp:
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        lines = vet_stamp.split("\n")
        sy = stamp_y - 10
        for line in lines:
            c.drawString(stamp_x + 10, sy, line)
            sy -= 11

    y -= 20

    # Fraud warning
    c.setFont("Helvetica", 6.5)
    c.setFillColor(HexColor("#666666"))
    fraud = (
        "Any person who knowingly and with intent to defraud any insurance company or other person files an application for insurance or "
        "statement of claim containing any materially false information, or conceals for the purpose of misleading, information concerning any "
        "fact material thereto, commits a fraudulent insurance act, which is a crime, and shall also be subject to a civil penalty not to exceed "
        "five thousand dollars and the stated value of the claim for each such violation."
    )
    lines = simpleSplit(fraud, "Helvetica", 6.5, PAGE_W - 2 * MARGIN)
    for line in lines:
        c.drawString(MARGIN, y, line)
        y -= 9

    y -= 15

    # Footer: submission methods
    c.setFillColor(BLUE)
    c.rect(0, y - 5, PAGE_W, 25, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, y, "Send the completed appeal form and documentation to:")

    y -= 30
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(DARK)
    methods = [
        ("MAIL TO:", "MetLife Pet Insurance\nClaims Department\n400 Missouri Avenue Suite 105\nJeffersonville, IN 47130"),
        ("EMAIL TO:", "Pet_Submit_Claim@metlife.com"),
        ("FAX TO:", "877-281-3348"),
        ("UPLOAD TO:", "Our Mobile App or\nMyPets Online Account"),
    ]
    col_w = (PAGE_W - 2 * MARGIN) / 4
    for i, (title, detail) in enumerate(methods):
        x = MARGIN + i * col_w
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(DARK)
        c.drawString(x, y, title)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(HexColor("#555555"))
        dy = y - 13
        for line in detail.split("\n"):
            c.drawString(x, dy, line)
            dy -= 10

    # Bottom copyright
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#999999"))
    c.drawCentredString(PAGE_W / 2, 30, "MetLife Pet Insurance | metlifepetinsurance.com")


def main():
    parser = argparse.ArgumentParser(description="Generate MetLife appeal form PDF")
    parser.add_argument("--fill", help="JSON file with form data")
    parser.add_argument("--output", "-o", default=None, help="Output PDF path")
    args = parser.parse_args()

    data = None
    if args.fill:
        with open(args.fill) as f:
            data = json.load(f)

    output = args.output
    if not output:
        output = "appeal-form-blank.pdf" if not data else "appeal-form-filled.pdf"

    c = canvas.Canvas(output, pagesize=letter)
    c.setTitle("MetLife Pet Insurance - Claim Appeal Form")
    draw_form(c, data)
    c.save()
    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
