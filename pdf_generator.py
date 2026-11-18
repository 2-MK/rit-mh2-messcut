"""Formal A4 PDF letter generator for Hostel Mess Cut Requests.
Engineered specifically for official academic submissions at RIT Kottayam (MH 2 Hostel).
Uses ReportLab to produce a standard formal institutional letter.
"""

from __future__ import annotations
import io
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from date_rules import (
    format_dd_mm_yyyy,
    get_today_dd_mm_yyyy,
    validate_complete_application
)


A4_WIDTH, A4_HEIGHT = A4  # 595.28 x 841.89 pt
MARGIN_X = 54.0
CONTENT_WIDTH = A4_WIDTH - (MARGIN_X * 2.0)

# Formal monochrome ink palette (authoritative black & charcoal)
COLOR_INK = colors.HexColor("#000000")
COLOR_MUTED = colors.HexColor("#333333")
COLOR_RULE = colors.HexColor("#444444")
COLOR_LIGHT_RULE = colors.HexColor("#aaaaaa")
COLOR_ROW_BG = colors.HexColor("#f9f9f9")


def sanitize_filename_part(text: str) -> str:
    """Sanitize student name for safe filename output."""
    clean = re.sub(r'[\\/*?:"<>|]', '', text or '')
    clean = re.sub(r'\s+', '_', clean.strip())
    return clean or "Student"


def build_pdf_filename(name: str, start_date_iso: str, end_date_iso: str) -> str:
    """Generate canonical filename e.g. Ajay_Nath_01-12-2026-14-12-2026.pdf."""
    safe_name = sanitize_filename_part(name)
    start_disp = format_dd_mm_yyyy(start_date_iso) or "Start"
    end_disp = format_dd_mm_yyyy(end_date_iso) or "End"
    return f"{safe_name}_{start_disp}-{end_disp}.pdf"


def wrap_text_to_width(c: canvas.Canvas, text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    """Wrap a long paragraph into lines fitting within max_width."""
    if not text:
        return [""]
    paragraphs = str(text).splitlines()
    result_lines = []

    for para in paragraphs:
        words = para.strip().split()
        if not words:
            continue
        current_line = words[0]
        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                result_lines.append(current_line)
                current_line = word
        result_lines.append(current_line)

    return result_lines if result_lines else [""]


def generate_mess_cut_pdf_buffer(
    profile: Dict[str, Any],
    request: Dict[str, Any],
    custom_date: Optional[str] = None
) -> Tuple[io.BytesIO, str]:
    """
    Generate a formal A4 Mess Cut Request Letter PDF as a BytesIO stream.
    Follows traditional formal Indian collegiate letter formatting.
    """
    eval_result = validate_complete_application(profile, request)
    if not eval_result["is_ready_for_export"]:
        issues = []
        if eval_result["missing_fields"]:
            issues.append(f"Missing required fields: {', '.join(eval_result['missing_fields'])}")
        if not eval_result["date_validation"]["is_valid"]:
            issues.append(f"Date error: {eval_result['date_validation']['message']}")
        raise ValueError("; ".join(issues))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    c.setTitle("Mess Cut Application - MH 2 Hostel, RIT Kottayam")
    c.setAuthor(profile.get("name", "Student"))
    c.setSubject("Application for Mess Cut")

    # Document details
    letter_date = custom_date or get_today_dd_mm_yyyy()
    name = (profile.get("name") or "").strip()
    admission_number = (profile.get("admissionNumber") or "").strip()
    semester = (profile.get("semester") or "").strip()
    branch = (profile.get("branch") or "").strip()
    reason = (request.get("reason") or "").strip()
    start_date_iso = request.get("startDate") or ""
    end_date_iso = request.get("endDate") or ""
    start_display = format_dd_mm_yyyy(start_date_iso)
    end_display = format_dd_mm_yyyy(end_date_iso)
    total_days = eval_result["date_validation"]["total_days"]
    days_text = f"{total_days} Days"

    # Start cursor
    y = A4_HEIGHT - 48.0

    # 1. Formal Institutional Letterhead (Centered, Academic)
    c.setFont("Times-Bold", 12.0)
    c.setFillColor(COLOR_INK)
    title_line1 = "RAJIV GANDHI INSTITUTE OF TECHNOLOGY, KOTTAYAM"
    c.drawCentredString(A4_WIDTH / 2.0, y, title_line1)
    y -= 15.0

    c.setFont("Times-Bold", 10.5)
    c.setFillColor(COLOR_MUTED)
    title_line2 = "MEN'S HOSTEL 2 (MH 2)"
    c.drawCentredString(A4_WIDTH / 2.0, y, title_line2)
    y -= 14.0

    c.setFont("Times-Bold", 11.0)
    c.setFillColor(COLOR_INK)
    title_line3 = "APPLICATION FOR MESS CUT"
    c.drawCentredString(A4_WIDTH / 2.0, y, title_line3)
    y -= 10.0

    # Institutional Double Divider Rule
    c.setStrokeColor(COLOR_RULE)
    c.setLineWidth(1.0)
    c.line(MARGIN_X, y, A4_WIDTH - MARGIN_X, y)
    y -= 2.0
    c.setLineWidth(0.4)
    c.line(MARGIN_X, y, A4_WIDTH - MARGIN_X, y)
    y -= 18.0

    # 2. Date and Place Row
    c.setFont("Times-Roman", 10.5)
    c.setFillColor(COLOR_INK)
    c.drawString(MARGIN_X, y, "Place: Kottayam")

    date_str = f"Date: {letter_date}"
    date_w = c.stringWidth(date_str, "Times-Roman", 10.5)
    c.drawString(A4_WIDTH - MARGIN_X - date_w, y, date_str)
    y -= 20.0

    # 3. Traditional Formal "From" Block
    c.setFont("Times-Bold", 10.5)
    c.drawString(MARGIN_X, y, "From:")
    y -= 14.0

    from_indent = MARGIN_X + 16.0
    c.setFont("Times-Bold", 10.5)
    c.drawString(from_indent, y, name)
    y -= 14.0

    c.setFont("Times-Roman", 10.5)
    from_lines = [
        f"Admission No.: {admission_number}",
        f"Semester: {semester}, Branch: {branch}",
        "MH 2 Hostel, RIT Kottayam"
    ]
    for line in from_lines:
        c.drawString(from_indent, y, line)
        y -= 14.0

    y -= 8.0

    # 4. Traditional Formal "To" Block
    c.setFont("Times-Bold", 10.5)
    c.drawString(MARGIN_X, y, "To:")
    y -= 14.0

    c.setFont("Times-Roman", 10.5)
    to_indent = MARGIN_X + 16.0
    to_lines = [
        "The Warden,",
        "MH 2 Hostel,",
        "RIT Kottayam."
    ]
    for line in to_lines:
        c.drawString(to_indent, y, line)
        y -= 14.0

    y -= 10.0

    # 5. Salutation
    c.setFont("Times-Roman", 10.5)
    c.drawString(MARGIN_X, y, "Respected Sir,")
    y -= 16.0

    # 6. Formal Subject Line (Underlined/Bold, standard Indian academic style)
    c.setFont("Times-Bold", 10.5)
    subject_text = f"Sub: Request for Mess Cut from {start_display} to {end_display} ({days_text}) - reg."
    c.drawString(MARGIN_X + 16.0, y, subject_text)
    subj_w = c.stringWidth(subject_text, "Times-Bold", 10.5)
    c.setLineWidth(0.5)
    c.setStrokeColor(COLOR_INK)
    c.line(MARGIN_X + 16.0, y - 2.0, MARGIN_X + 16.0 + subj_w, y - 2.0)
    y -= 20.0

    # 7. Opening Paragraph
    c.setFont("Times-Roman", 10.5)
    opening_p = (
        f"I am a resident of MH 2 Hostel, currently studying in {semester}, {branch}. "
        f"I respectfully request you to kindly grant me a mess cut for a period of {total_days} days, "
        f"commencing from {start_display} to {end_display} (both days inclusive), as {reason}."
    )
    wrapped_open = wrap_text_to_width(c, opening_p, "Times-Roman", 10.5, CONTENT_WIDTH)
    for i, line in enumerate(wrapped_open):
        line_x = MARGIN_X + 18.0 if i == 0 else MARGIN_X
        c.drawString(line_x, y, line)
        y -= 15.0

    y -= 8.0

    # 8. Formal Structured Summary Table
    col1_w = 150.0
    col2_w = CONTENT_WIDTH - col1_w

    table_data = [
        ("Student Name", name),
        ("Admission Number", admission_number),
        ("Semester & Branch", f"{semester}, {branch}"),
        ("Mess Cut Duration", f"{total_days} Days (Inclusive)"),
        ("Inclusive Dates", f"{start_display} to {end_display}"),
        ("Reason for Absence", reason),
    ]

    for label, val in table_data:
        wrapped_val = wrap_text_to_width(c, val, "Times-Roman", 9.5, col2_w - 16.0)
        row_h = max(20.0, (len(wrapped_val) * 13.0) + 8.0)
        row_bottom = y - row_h

        # Light zebra fill
        c.setFillColor(COLOR_ROW_BG)
        c.rect(MARGIN_X, row_bottom, col1_w, row_h, fill=1, stroke=0)

        # Hairline border strokes
        c.setStrokeColor(COLOR_LIGHT_RULE)
        c.setLineWidth(0.5)
        c.rect(MARGIN_X, row_bottom, col1_w, row_h, fill=0, stroke=1)
        c.rect(MARGIN_X + col1_w, row_bottom, col2_w, row_h, fill=0, stroke=1)

        # Label text
        c.setFont("Times-Bold", 9.5)
        c.setFillColor(COLOR_INK)
        c.drawString(MARGIN_X + 8.0, y - 13.0, label)

        # Value text
        c.setFont("Times-Roman", 9.5)
        val_y = y - 13.0
        for vline in wrapped_val:
            c.drawString(MARGIN_X + col1_w + 8.0, val_y, vline)
            val_y -= 13.0

        y = row_bottom

    y -= 16.0

    # 9. Concluding Declaration Paragraph
    declaration_p = (
        "I hereby declare that I will not be consuming food or availing of hostel mess facilities "
        "during the aforementioned period. I kindly request you to approve my application and make the "
        "eligible deduction in my monthly mess dues as per hostel regulations."
    )
    wrapped_decl = wrap_text_to_width(c, declaration_p, "Times-Roman", 10.5, CONTENT_WIDTH)
    for i, line in enumerate(wrapped_decl):
        line_x = MARGIN_X + 18.0 if i == 0 else MARGIN_X
        c.drawString(line_x, y, line)
        y -= 15.0

    y -= 12.0

    # 10. Formal Sign-off (Bottom Left)
    signoff_x = MARGIN_X
    c.setFont("Times-Roman", 10.5)
    c.drawString(signoff_x, y, "Yours faithfully,")
    y -= 38.0  # Generous signature gap

    c.setFont("Times-Bold", 10.5)
    c.drawString(signoff_x, y, name)
    y -= 14.0
    c.setFont("Times-Roman", 10.0)
    c.drawString(signoff_x, y, f"Adm No: {admission_number}")
    y -= 14.0
    c.drawString(signoff_x, y, f"{semester}, {branch}")
    c.showPage()
    c.save()

    buffer.seek(0)
    filename = build_pdf_filename(name, start_date_iso, end_date_iso)
    return buffer, filename


def save_mess_cut_pdf_file(
    profile: Dict[str, Any],
    request: Dict[str, Any],
    output_dir: str = "output",
    custom_date: Optional[str] = None
) -> str:
    """Generate and save PDF to filesystem. Returns full filepath."""
    os.makedirs(output_dir, exist_ok=True)
    buf, filename = generate_mess_cut_pdf_buffer(profile, request, custom_date=custom_date)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(buf.getvalue())
    return filepath
