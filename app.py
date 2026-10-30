"""
First Aid Tutors — Invoice & Receipt Generator
Run: python app.py
Requires: pip install reportlab pillow
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime
from pathlib import Path

# ── PDF engine ──────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Colours ──────────────────────────────────────────────────────────────────
RED      = colors.HexColor("#C0392B")
DARK     = colors.HexColor("#1A1A2E")
MIDGREY  = colors.HexColor("#6B7280")
LIGHTBG  = colors.HexColor("#F8F9FA")
WHITE    = colors.white
ACCENT   = colors.HexColor("#E8F4FD")

# ── Fixed company data ────────────────────────────────────────────────────────
COMPANY = {
    "name":    "FAIRVIEW TRAINING LTD",
    "trading": "Trading as FIRST AID TUTORS",
    "address": "Room 103, 10 Courtenay Road, East Lane Business Park,\nWembley, Middlesex HA9 7ND",
    "vat":     "468568531",
    "email":   "info@firstaidtutors.co.uk",
    "phone":   "020 2821 27315",
    "mobile":  "07868 176325",
    "website": "www.firstaidtutors.co.uk",
    "bank":    "Metro Bank",
    "sort":    "23-05-80",
    "account": "17792458",
    "accname": "FAIRVIEW TRAINING",
}

def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

# Logo (inside EXE)
LOGO_PATH = resource_path("logo.png")

# Settings file — counters, save location, history (up to 5000), course library
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), "fat_generator_settings.json")
MAX_HISTORY   = 5000
WARN_HISTORY  = 4500   # show a warning badge when approaching the cap

# Default course library (price inclusive of VAT)
DEFAULT_COURSES = [
    {"name": "Emergency First Aid at Work",                                                           "price_inc": 108.00, "vat_rate": 20},
    {"name": "Paediatric 12 Hour Infant / Child First Aid Level 3 (VTQ) – Classroom Blended Part 2", "price_inc": 108.00, "vat_rate": 20},
    {"name": "BLS, AED & Anaphylaxis for Adults & Children - FAA Level 3",                           "price_inc":  72.00, "vat_rate": 20},
    {"name": "Immediate Life Support (ILS) Level 3 (VTQ) for Healthcare Professionals",              "price_inc": 118.80, "vat_rate": 20},
    {"name": "Paediatric Immediate Life Support (PILS) Level 3 (VTQ)",                               "price_inc": 118.80, "vat_rate": 20},
    {"name": "Basic Life Support and AED for Healthcare Professionals Level 2 (VTQ)",                "price_inc":  72.00, "vat_rate": 20},
    {"name": "CPR/BLS, AED and Anaphylaxis Level 2 (VTQ)",                                           "price_inc":  72.00, "vat_rate": 20},
    {"name": "Dental Basic Life Support (BLS) and AED Level 2 (VTQ)",                                "price_inc":  72.00, "vat_rate": 20},
    {"name": "Dental Immediate Life Support (ILS) Level 3 (VTQ)",                                    "price_inc": 118.80, "vat_rate": 20},
    {"name": "First Aid at Work",                                                                     "price_inc": 216.00, "vat_rate": 20},
]


def _load_settings() -> dict:
    import json
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_settings(settings: dict):
    """Write to a temp file first, then swap it in, so a crash never corrupts history."""
    import json
    tmp_path = SETTINGS_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, SETTINGS_FILE)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def _parse_date_from_field(date_str: str):
    formats = ["%d %B %Y", "%#d %B %Y", "%-d %B %Y",
               "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.today()


def _get_next_doc_number(doc_type: str, date_str: str = "") -> str:
    parsed   = _parse_date_from_field(date_str) if date_str else datetime.today()
    date_key = parsed.strftime("%d%m%y")
    prefix   = "FT" if doc_type == "invoice" else "FAT"
    key      = f"{prefix}-{date_key}"
    settings = _load_settings()
    counters = settings.get("counters", {})
    count    = counters.get(key, 0) + 1
    counters[key] = count
    settings["counters"] = counters
    _save_settings(settings)
    return f"{key}-{count:02d}"


def _preview_doc_number(doc_type: str, date_str: str = "") -> str:
    parsed   = _parse_date_from_field(date_str) if date_str else datetime.today()
    date_key = parsed.strftime("%d%m%y")
    prefix   = "FT" if doc_type == "invoice" else "FAT"
    key      = f"{prefix}-{date_key}"
    settings = _load_settings()
    next_n   = settings.get("counters", {}).get(key, 0) + 1
    return f"{key}-{next_n:02d}"


def _get_saved_location() -> str:
    saved = _load_settings().get("last_save_dir", "")
    if saved and os.path.isdir(saved):
        return saved
    return str(Path.home() / "Documents")


def _save_location(path: str):
    s = _load_settings()
    s["last_save_dir"] = path
    _save_settings(s)


def _save_history_entry(entry: dict):
    """Prepend entry; keep newest MAX_HISTORY, never silently drop — warn instead."""
    s = _load_settings()
    history = s.get("history", [])
    history.insert(0, entry)
    if len(history) > MAX_HISTORY:
        history = history[:MAX_HISTORY]   # trim oldest
    s["history"] = history
    _save_settings(s)


def _load_history() -> list:
    return _load_settings().get("history", [])


BACKUP_DIR  = os.path.join(os.path.expanduser("~"), "fat_generator_backups")
BACKUP_KEEP = 30   # number of daily backups to keep


def _backup_settings_daily():
    """Copy the settings/history file once per day before anything changes it."""
    import shutil
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        target = os.path.join(BACKUP_DIR,
                              f"fat_generator_settings_{datetime.today().strftime('%Y-%m-%d')}.json")
        if not os.path.exists(target):
            shutil.copy2(SETTINGS_FILE, target)
        backups = sorted(f for f in os.listdir(BACKUP_DIR)
                         if f.startswith("fat_generator_settings_") and f.endswith(".json"))
        for old in backups[:-BACKUP_KEEP]:
            os.remove(os.path.join(BACKUP_DIR, old))
    except Exception:
        pass


def _pdf_path(out_dir: str, doc_type: str, number: str, client_name: str) -> str:
    """Build a unique PDF path such as invoice_FT-301026-01_Jane_Smith.pdf.
    Never returns the path of an existing file, so earlier PDFs are never overwritten."""
    import re
    label     = "invoice" if doc_type == "invoice" else "receipt"
    name_safe = re.sub(r"[^\w\-]", "", client_name.replace(" ", "_")) or "client"
    base      = f"{label}_{number}_{name_safe}"
    path      = os.path.join(out_dir, f"{base}.pdf")
    n = 2
    while os.path.exists(path):
        path = os.path.join(out_dir, f"{base}_{n}.pdf")
        n += 1
    return path


def _same_entry(a: dict, b: dict) -> bool:
    return (a.get("number") == b.get("number")
            and a.get("doc_type") == b.get("doc_type")
            and a.get("generated_at") == b.get("generated_at"))


def _update_history_entry(target: dict, changes: dict) -> bool:
    """Apply changes to one stored history entry. Returns True if it was found."""
    s = _load_settings()
    history = s.get("history", [])
    for e in history:
        if _same_entry(e, target):
            e.update(changes)
            s["history"] = history
            _save_settings(s)
            return True
    return False


EXPORT_COLUMNS = [
    ("Type",             lambda e: "Invoice" if e.get("doc_type") == "invoice" else "Receipt"),
    ("Number",           lambda e: e.get("number", "")),
    ("Document Date",    lambda e: e.get("date", "")),
    ("Generated At",     lambda e: e.get("generated_at", "").replace("T", " ")),
    ("Client Name",      lambda e: e.get("client_name", "")),
    ("Client Email",     lambda e: e.get("client_email", "")),
    ("Client Phone",     lambda e: e.get("client_phone", "")),
    ("Client Address",   lambda e: e.get("client_address", "").replace("\n", ", ")),
    ("Course",           lambda e: e.get("description", "")),
    ("Course Date",      lambda e: e.get("course_date", "")),
    ("Amount Exc. VAT",  lambda e: _money(e.get("amount_exc"))),
    ("VAT Rate %",       lambda e: e.get("vat_rate", "")),
    ("VAT Amount",       lambda e: _money(_vat_parts(e)[0])),
    ("Total Inc. VAT",   lambda e: _money(_vat_parts(e)[1])),
    ("Status",           lambda e: e.get("status", "")),
    ("Linked Document",  lambda e: e.get("receipt_number", "") or e.get("from_invoice", "")),
]


def _vat_parts(entry: dict):
    """Return (vat_amount, total) as floats, or ("", "") if the numbers are unreadable."""
    try:
        exc  = float(entry.get("amount_exc", 0))
        rate = float(entry.get("vat_rate", 20))
        vat  = exc * rate / 100
        return vat, exc + vat
    except (TypeError, ValueError):
        return "", ""


def _money(value) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return ""


def export_history_csv(entries: list, out_path: str):
    """Write history entries to a CSV file that opens cleanly in Excel."""
    import csv
    # utf-8-sig adds a BOM so Excel shows £ and accented names correctly
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([name for name, _ in EXPORT_COLUMNS])
        for e in entries:
            writer.writerow([getter(e) for _, getter in EXPORT_COLUMNS])


def _load_courses() -> list:
    s = _load_settings()
    if "courses" not in s:
        s["courses"] = DEFAULT_COURSES
        _save_settings(s)
    return s.get("courses", DEFAULT_COURSES)


def _save_courses(courses: list):
    s = _load_settings()
    s["courses"] = courses
    _save_settings(s)

# ─────────────────────────────────────────────────────────────────────────────
#  PDF BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _base_styles():
    return {
        "company":  ParagraphStyle("company",  fontName="Helvetica-Bold",   fontSize=14, textColor=DARK,    leading=18, alignment=TA_CENTER),
        "trading":  ParagraphStyle("trading",  fontName="Helvetica-Oblique",fontSize=9,  textColor=MIDGREY, leading=13, alignment=TA_CENTER),
        "address":  ParagraphStyle("address",  fontName="Helvetica",        fontSize=8,  textColor=MIDGREY, leading=12, alignment=TA_CENTER),
        "doctype":  ParagraphStyle("doctype",  fontName="Helvetica-Bold",   fontSize=22, textColor=RED,     leading=28, alignment=TA_CENTER),
        "label":    ParagraphStyle("label",    fontName="Helvetica-Bold",   fontSize=8,  textColor=MIDGREY, leading=11, spaceAfter=1),
        "value":    ParagraphStyle("value",    fontName="Helvetica",        fontSize=9,  textColor=DARK,    leading=13),
        "valuebold":ParagraphStyle("valuebold",fontName="Helvetica-Bold",   fontSize=9,  textColor=DARK,    leading=13),
        "small":    ParagraphStyle("small",    fontName="Helvetica",        fontSize=7.5,textColor=MIDGREY, leading=11),
        "footer":   ParagraphStyle("footer",   fontName="Helvetica",        fontSize=7,  textColor=MIDGREY, leading=10, alignment=TA_CENTER),
    }


def _header_block(story, styles, doc_type_label):
    """Logo + company name + doc type banner."""
    # Logo (optional)
    if os.path.exists(LOGO_PATH):
        try:
            img = RLImage(LOGO_PATH, width=40*mm, height=20*mm)
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 3*mm))
        except Exception:
            pass

    story.append(Paragraph(COMPANY["name"], styles["company"]))
    story.append(Paragraph(COMPANY["trading"], styles["trading"]))
    story.append(Spacer(1, 1*mm))
    story.append(Paragraph(COMPANY["address"].replace("\n","<br/>"), styles["address"]))
    story.append(Paragraph(f"VAT Number: {COMPANY['vat']}", styles["address"]))
    story.append(Spacer(1, 4*mm))

    # Red banner
    banner_data = [[Paragraph(doc_type_label, styles["doctype"])]]
    banner = Table(banner_data, colWidths=[170*mm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHTBG),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("LINEBELOW", (0,0), (-1,-1), 1.5, RED),
    ]))
    story.append(banner)
    story.append(Spacer(1, 6*mm))


def _two_col(styles, left_pairs, right_pairs):
    """Render two columns of label/value pairs side by side."""
    def make_rows(pairs):
        rows = []
        for lbl, val in pairs:
            if isinstance(val, Paragraph):
                rows.append([Paragraph(lbl, styles["label"]), ""])
                rows.append([val, ""])
            else:
                rows.append([Paragraph(lbl, styles["label"]), ""])
                rows.append([Paragraph(str(val), styles["value"]), ""])
            rows.append([Spacer(1, 2*mm), ""])
        return rows

    left_rows  = make_rows(left_pairs)
    right_rows = make_rows(right_pairs)

    # Pad shorter side
    while len(left_rows) < len(right_rows):
        left_rows.append([Spacer(1, 1), ""])
    while len(right_rows) < len(left_rows):
        right_rows.append([Spacer(1, 1), ""])

    # Build a flat table: col0 = left label, col1 = spacer, col2 = right label
    combined = []
    for l, r in zip(left_rows, right_rows):
        combined.append([l[0], Spacer(6*mm, 1), r[0]])

    tbl = Table(combined, colWidths=[88*mm, 6*mm, 76*mm])
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",    (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return tbl


def _line_items_table(styles, exc_vat, vat_rate, total, status_text, paid=False):
    """The financial summary table."""
    vat_label   = f"VAT ({vat_rate}%)"
    total_label = "Total Paid (Incl. VAT)" if paid else "Total (Incl. VAT)"

    # Status pill colour
    if "paid" in status_text.lower():
        pill_bg, pill_fg = colors.HexColor("#D4EDDA"), colors.HexColor("#155724")
    else:
        pill_bg, pill_fg = colors.HexColor("#FDECEA"), RED

    status_style = ParagraphStyle("stat", fontName="Helvetica-Bold", fontSize=9,
                                  textColor=pill_fg, alignment=TA_CENTER)

    data = [
        [Paragraph("DESCRIPTION", styles["label"]),
         Paragraph("AMOUNT", styles["label"])],
        [Paragraph("Amount (Excl. VAT)", styles["value"]),
         Paragraph(f"£{exc_vat:.2f}", styles["value"])],
        [Paragraph(vat_label, styles["value"]),
         Paragraph(f"£{(exc_vat * vat_rate / 100):.2f}", styles["value"])],
        [Paragraph(f"<b>{total_label}</b>",
                   ParagraphStyle("tot", fontName="Helvetica-Bold", fontSize=10, textColor=DARK)),
         Paragraph(f"<b>£{total:.2f}</b>",
                   ParagraphStyle("totval", fontName="Helvetica-Bold", fontSize=10, textColor=RED))],
        [Paragraph("Payment Status", styles["label"]),
         Paragraph(status_text, status_style)],
    ]

    t = Table(data, colWidths=[115*mm, 55*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  DARK),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  8),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-2), [WHITE, LIGHTBG]),
        ("BACKGROUND",    (0,3), (-1,3),  ACCENT),
        ("BACKGROUND",    (1,4), (1,4),   pill_bg),
        ("LINEABOVE",     (0,3), (-1,3),  1.5, RED),
        ("LINEBELOW",     (0,-1),(-1,-1), 0.5, MIDGREY),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
    ]))
    return t


def _footer(story, styles, include_bank=False):
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MIDGREY))
    story.append(Spacer(1, 3*mm))

    if include_bank:
        bank_data = [[
            Paragraph("BANK PAYMENT DETAILS", styles["label"]),
            Paragraph("", styles["label"]),
            Paragraph("", styles["label"]),
        ],[
            Paragraph(f"Bank: <b>{COMPANY['bank']}</b>", styles["small"]),
            Paragraph(f"Sort Code: <b>{COMPANY['sort']}</b>", styles["small"]),
            Paragraph(f"Acc. Number: <b>{COMPANY['account']}</b>", styles["small"]),
        ],[
            Paragraph(f"Acc. Name: <b>{COMPANY['accname']}</b>", styles["small"]),
            Paragraph("", styles["small"]),
            Paragraph("", styles["small"]),
        ]]
        bt = Table(bank_data, colWidths=[60*mm, 55*mm, 55*mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), LIGHTBG),
            ("SPAN",          (0,0), (-1,0)),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
        ]))
        story.append(bt)
        story.append(Spacer(1, 4*mm))

    contact = f"{COMPANY['email']}  |  {COMPANY['phone']}  |  {COMPANY['website']}"
    story.append(Paragraph(contact, styles["footer"]))
    story.append(Paragraph(
        f"{COMPANY['name']} — Registered in England & Wales  |  VAT: {COMPANY['vat']}",
        styles["footer"]
    ))


def generate_invoice(data: dict, out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=20*mm, rightMargin=20*mm
    )
    styles = _base_styles()
    story  = []

    _header_block(story, styles, "VAT INVOICE")

    # Contact row under header
    contact_info = (
        f"<b>Email:</b> {COMPANY['email']}  |  "
        f"<b>Phone:</b> {COMPANY['phone']}  |  "
        f"<b>Mobile:</b> {COMPANY['mobile']}  |  "
        f"<b>Web:</b> {COMPANY['website']}"
    )
    story.append(Paragraph(contact_info,
                            ParagraphStyle("ci", fontName="Helvetica", fontSize=7.5,
                                           textColor=MIDGREY, leading=11, alignment=TA_CENTER)))
    story.append(Spacer(1, 5*mm))

    # Bill To + Invoice details
    bill_to = (
        f"{data['client_name']}<br/>"
        f"{data['client_address'].replace(chr(10), '<br/>')}<br/>"
        f"<b>Phone:</b> {data['client_phone']}<br/>"
        f"<b>Email:</b> {data['client_email']}"
    )
    left  = [("BILL TO", Paragraph(bill_to, styles["value"]))]
    right = [
        ("INVOICE DATE",   data["date"]),
        ("INVOICE NUMBER", data["number"]),
    ]
    story.append(_two_col(styles, left, right))
    story.append(Spacer(1, 5*mm))

    # Course description block
    desc_data = [
        [Paragraph("COURSE DESCRIPTION", styles["label"])],
        [Paragraph(data["description"], styles["value"])],
        [Paragraph(f"Course Date: <b>{data['course_date']}</b>",
                   ParagraphStyle("cd", fontName="Helvetica", fontSize=8.5,
                                  textColor=MIDGREY, leading=12))],
    ]
    dt = Table(desc_data, colWidths=[170*mm])
    dt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0), DARK),
        ("TEXTCOLOR",     (0,0), (0,0), WHITE),
        ("FONTSIZE",      (0,0), (0,0), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHTBG]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
    ]))
    story.append(dt)
    story.append(Spacer(1, 5*mm))

    exc = float(data["amount_exc"])
    rate = float(data["vat_rate"])
    total = exc * (1 + rate / 100)
    story.append(_line_items_table(styles, exc, rate, total, data["status"], paid=False))

    _footer(story, styles, include_bank=True)
    doc.build(story)


def generate_receipt(data: dict, out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=20*mm, rightMargin=20*mm
    )
    styles = _base_styles()
    story  = []

    _header_block(story, styles, "RECEIPT")

    # Contact row under header (receipt shows all contacts)
    contact_info = (
        f"<b>Email:</b> {COMPANY['email']}  |  "
        f"<b>Phone:</b> {COMPANY['phone']}  |  "
        f"<b>Mobile:</b> {COMPANY['mobile']}  |  "
        f"<b>Web:</b> {COMPANY['website']}"
    )
    story.append(Paragraph(contact_info,
                            ParagraphStyle("ci", fontName="Helvetica", fontSize=7.5,
                                           textColor=MIDGREY, leading=11, alignment=TA_CENTER)))
    story.append(Spacer(1, 5*mm))

    bill_to = (
        f"{data['client_name']}<br/>"
        f"{data['client_address'].replace(chr(10), '<br/>')}<br/>"
        f"<b>Phone:</b> {data['client_phone']}<br/>"
        f"<b>Email:</b> {data['client_email']}"
    )
    left  = [("RECEIVED FROM", Paragraph(bill_to, styles["value"]))]
    right = [
        ("RECEIPT DATE",   data["date"]),
        ("RECEIPT NUMBER", data["number"]),
    ]
    story.append(_two_col(styles, left, right))
    story.append(Spacer(1, 5*mm))

    desc_data = [
        [Paragraph("COURSE DESCRIPTION", styles["label"])],
        [Paragraph(data["description"], styles["value"])],
        [Paragraph(f"Course Date: <b>{data['course_date']}</b>",
                   ParagraphStyle("cd", fontName="Helvetica", fontSize=8.5,
                                  textColor=MIDGREY, leading=12))],
    ]
    dt = Table(desc_data, colWidths=[170*mm])
    dt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0), DARK),
        ("TEXTCOLOR",     (0,0), (0,0), WHITE),
        ("FONTSIZE",      (0,0), (0,0), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LIGHTBG]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
    ]))
    story.append(dt)
    story.append(Spacer(1, 5*mm))

    exc = float(data["amount_exc"])
    rate = float(data["vat_rate"])
    total = exc * (1 + rate / 100)
    story.append(_line_items_table(styles, exc, rate, total, data["status"], paid=True))

    _footer(story, styles, include_bank=False)
    doc.build(story)


# ─────────────────────────────────────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    # ── colour palette ──────────────────────────────────────────────────────
    BG       = "#F0F2F5"
    PANEL    = "#FFFFFF"
    ACCENT   = "#C0392B"
    ACCENT2  = "#E74C3C"
    DARK     = "#1A1A2E"
    MUTED    = "#6B7280"
    BORDER   = "#E5E7EB"
    SUCCESS  = "#27AE60"
    INP_BG   = "#F8F9FA"
    INP_FG   = "#1A1A2E"
    FONT     = ("Segoe UI", 10)
    FONT_B   = ("Segoe UI", 10, "bold")
    FONT_H   = ("Segoe UI", 14, "bold")
    FONT_SH  = ("Segoe UI", 9)

    def __init__(self):
        super().__init__()
        self.title("First Aid Tutors — Document Generator")
        self.geometry("720x820")
        self.resizable(True, True)
        self.configure(bg=self.BG)
        self._doc_type = tk.StringVar(value="invoice")
        self._build_ui()

    # ── UI scaffolding ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=self.DARK, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="⛑", font=("Segoe UI Emoji", 22),
                 bg=self.DARK, fg=self.ACCENT).pack(side="left", padx=(20, 6), pady=10)
        tk.Label(header, text="First Aid Tutors", font=("Segoe UI", 15, "bold"),
                 bg=self.DARK, fg="white").pack(side="left", pady=10)
        tk.Label(header, text="Document Generator", font=("Segoe UI", 10),
                 bg=self.DARK, fg="#9CA3AF").pack(side="left", padx=(6,0), pady=10)

        # ── Scrollable main area ─────────────────────────────────────────────
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True, padx=0, pady=0)

        canvas = tk.Canvas(outer, bg=self.BG, highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._scroll_frame = tk.Frame(canvas, bg=self.BG)
        self._win_id = canvas.create_window((0, 0), window=self._scroll_frame,
                                             anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self._win_id, width=canvas.winfo_width())

        self._scroll_frame.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._win_id, width=canvas.winfo_width()))

        # Mouse-wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._populate(self._scroll_frame)

    def _populate(self, parent):
        # ── History panel ────────────────────────────────────────────────────
        hist_outer = tk.Frame(parent, bg=self.PANEL, bd=0, relief="flat",
                              highlightthickness=1, highlightbackground=self.BORDER)
        hist_outer.pack(fill="x", padx=18, pady=(14, 0))

        hist_hdr = tk.Frame(hist_outer, bg=self.DARK)
        hist_hdr.pack(fill="x")
        self._hist_count_lbl = tk.Label(hist_hdr, text="🕐  Document History",
                 font=self.FONT_B, bg=self.DARK, fg="white")
        self._hist_count_lbl.pack(side="left", padx=12, pady=8)
        tk.Label(hist_hdr,
                 text="Double-click a row to reload into the form (date set to today)",
                 font=self.FONT_SH, bg=self.DARK, fg="#9CA3AF").pack(side="left", padx=(0, 8))

        search_frame = tk.Frame(hist_outer, bg=self.BG)
        search_frame.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(search_frame, text="Search:", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).pack(side="left")
        self._hist_search = tk.Entry(search_frame, font=self.FONT_SH,
                                     bg=self.INP_BG, fg=self.INP_FG,
                                     relief="flat", bd=0,
                                     highlightthickness=1, highlightbackground=self.BORDER)
        self._hist_search.pack(side="left", fill="x", expand=True,
                               ipady=5, ipadx=6, padx=(6, 0))
        self._hist_search.bind("<KeyRelease>", lambda *_: self._refresh_history())
        tk.Button(search_frame, text="⬇ Export CSV", font=self.FONT_SH,
                  bg=self.DARK, fg="white", activebackground=self.ACCENT,
                  activeforeground="white", relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=4,
                  command=self._export_history).pack(side="left", padx=(8, 0))
        tk.Button(search_frame, text="✅ Mark Paid → Receipt", font=self.FONT_SH,
                  bg=self.SUCCESS, fg="white", activebackground=self.DARK,
                  activeforeground="white", relief="flat", bd=0,
                  cursor="hand2", padx=10, pady=4,
                  command=self._invoice_to_receipt).pack(side="left", padx=(6, 0))

        lb_frame = tk.Frame(hist_outer, bg=self.BG)
        lb_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._hist_lb = tk.Listbox(
            lb_frame, height=5, font=("Courier New", 9),
            bg=self.INP_BG, fg=self.INP_FG,
            selectbackground=self.ACCENT, selectforeground="white",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self.BORDER,
            activestyle="none",
        )
        lb_scroll = ttk.Scrollbar(lb_frame, orient="vertical", command=self._hist_lb.yview)
        self._hist_lb.configure(yscrollcommand=lb_scroll.set)
        lb_scroll.pack(side="right", fill="y")
        self._hist_lb.pack(side="left", fill="x", expand=True)
        self._hist_lb.bind("<Double-Button-1>", self._load_from_history)
        self._hist_lb.bind("<Return>",          self._load_from_history)

        self._hist_menu = tk.Menu(self, tearoff=0)
        self._hist_menu.add_command(label="✅  Mark Paid → Create Receipt",
                                    command=self._invoice_to_receipt)
        self._hist_menu.add_command(label="✏️  Load into Form",
                                    command=self._load_from_history)
        def _on_right_click(event):
            idx = self._hist_lb.nearest(event.y)
            if idx < 0 or idx >= self._hist_lb.size():
                return
            self._hist_lb.selection_clear(0, "end")
            self._hist_lb.selection_set(idx)
            self._hist_lb.activate(idx)
            try:
                self._hist_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._hist_menu.grab_release()
        self._hist_lb.bind("<Button-3>", _on_right_click)   # Windows / Linux
        self._hist_lb.bind("<Button-2>", _on_right_click)   # macOS

        self._history_filtered = []
        self._refresh_history()

        self._divider(parent)

        # ── Doc type toggle ──────────────────────────────────────────────────
        toggle_frame = tk.Frame(parent, bg=self.BG)
        toggle_frame.pack(fill="x", padx=18, pady=(18, 0))

        tk.Label(toggle_frame, text="Document Type", font=self.FONT_B,
                 bg=self.BG, fg=self.DARK).pack(anchor="w")
        tk.Label(toggle_frame, text="Select what you want to generate",
                 font=self.FONT_SH, bg=self.BG, fg=self.MUTED).pack(anchor="w")

        btn_row = tk.Frame(toggle_frame, bg=self.BG)
        btn_row.pack(anchor="w", pady=(8, 0))

        self._inv_btn = self._toggle_btn(btn_row, "🧾  Invoice", "invoice")
        self._inv_btn.pack(side="left", padx=(0, 8))
        self._rec_btn = self._toggle_btn(btn_row, "✅  Receipt", "receipt")
        self._rec_btn.pack(side="left")
        self._doc_type.trace_add("write", lambda *_: self._refresh_toggle())
        self._refresh_toggle()

        self._divider(parent)

        # ── Client info ──────────────────────────────────────────────────────
        self._section(parent, "👤  Client Information")
        client_grid = tk.Frame(parent, bg=self.BG)
        client_grid.pack(fill="x", padx=18, pady=(0,0))

        self.f_name    = self._field(client_grid, "Full Name *",         row=0, col=0)
        self.f_address = self._field(client_grid, "Address *",           row=1, col=0, multiline=True)
        self.f_phone   = self._field(client_grid, "Phone Number *",      row=2, col=0)
        self.f_email   = self._field(client_grid, "Email Address *",     row=2, col=1)

        self._divider(parent)

        # ── Document details ─────────────────────────────────────────────────
        self._section(parent, "📄  Document Details")
        doc_grid = tk.Frame(parent, bg=self.BG)
        doc_grid.pack(fill="x", padx=18)

        _today = datetime.today()
        _day_fmt = "%#d" if sys.platform == "win32" else "%-d"
        self.f_date   = self._field(doc_grid, "Date *",          row=0, col=0,
                                    placeholder=_today.strftime(f"{_day_fmt} %B %Y"))

        # Document number — auto-generated, shown read-only
        num_cell = tk.Frame(doc_grid, bg=self.BG)
        num_cell.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0, 10))
        doc_grid.columnconfigure(0, weight=1)
        doc_grid.columnconfigure(1, weight=1)
        tk.Label(num_cell, text="Document Number (auto)", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).pack(anchor="w")
        self._doc_num_var = tk.StringVar(value=self._default_number())
        self._doc_type.trace_add("write", self._refresh_doc_number)
        num_display = tk.Label(num_cell, textvariable=self._doc_num_var,
                               font=("Segoe UI", 10, "bold"),
                               bg=self.INP_BG, fg=self.ACCENT,
                               relief="flat", bd=0, anchor="w", padx=8, pady=8,
                               highlightthickness=1, highlightbackground=self.BORDER)
        num_display.pack(fill="x", pady=(3, 0))
        self.f_date.bind("<KeyRelease>", self._refresh_doc_number)
        self.f_date.bind("<FocusOut>",   self._refresh_doc_number)

        self._divider(parent)

        # ── Course details ───────────────────────────────────────────────────
        self._section(parent, "🏫  Course Details")
        course_grid = tk.Frame(parent, bg=self.BG)
        course_grid.pack(fill="x", padx=18)
        course_grid.columnconfigure(0, weight=1)
        course_grid.columnconfigure(1, weight=1)

        # Course picker
        picker_cell = tk.Frame(course_grid, bg=self.BG)
        picker_cell.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 6))
        tk.Label(picker_cell, text="Select from Course Library",
                 font=self.FONT_SH, bg=self.BG, fg=self.MUTED).pack(anchor="w")
        picker_row = tk.Frame(picker_cell, bg=self.BG)
        picker_row.pack(fill="x", pady=(3, 0))

        self._course_var = tk.StringVar(value="— select a course —")
        self._course_combo = ttk.Combobox(picker_row, textvariable=self._course_var,
                                          state="readonly", font=self.FONT_SH, width=54)
        self._course_combo.pack(side="left", fill="x", expand=True, ipady=5)
        self._style_combo(self._course_combo)
        self._course_combo.bind("<<ComboboxSelected>>", self._on_course_selected)

        tk.Button(picker_row, text="⚙ Manage Courses",
                  font=self.FONT_SH, bg=self.BORDER, fg=self.DARK,
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=6,
                  command=self._open_course_manager).pack(side="left", padx=(8, 0))

        self._refresh_course_combo()

        self.f_desc  = self._field(course_grid, "Course Description *", row=1, col=0,
                                    multiline=True, colspan=2)
        self.f_cdate = self._field(course_grid, "Course Date *",         row=2, col=0)

        self._divider(parent)

        # ── Financials ───────────────────────────────────────────────────────
        self._section(parent, "💷  Financial Details")
        fin_grid = tk.Frame(parent, bg=self.BG)
        fin_grid.pack(fill="x", padx=18)

        self.f_exc  = self._field(fin_grid, "Amount (Excl. VAT) £ *", row=0, col=0, placeholder="0.00")
        self.f_vat  = self._field(fin_grid, "VAT Rate % *",            row=0, col=1, placeholder="20")

        # Live total preview
        self._total_var = tk.StringVar(value="Total (Incl. VAT): —")
        total_lbl = tk.Label(fin_grid, textvariable=self._total_var,
                             font=("Segoe UI", 10, "bold"),
                             bg=self.BG, fg=self.ACCENT)
        total_lbl.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6,0))

        for w in [self.f_exc, self.f_vat]:
            w.bind("<KeyRelease>", self._update_total)

        self._divider(parent)

        # ── Status ───────────────────────────────────────────────────────────
        self._section(parent, "🔖  Payment Status")
        status_frame = tk.Frame(parent, bg=self.BG)
        status_frame.pack(fill="x", padx=18)

        self._status_var = tk.StringVar(value="Payment Outstanding")
        statuses = ["Payment Outstanding", "Paid", "Partially Paid", "Awaiting Bank Transfer", "Refunded"]
        status_combo = ttk.Combobox(status_frame, textvariable=self._status_var,
                                    values=statuses, state="readonly",
                                    font=self.FONT, width=34)
        status_combo.pack(anchor="w", pady=(4,0))
        self._style_combo(status_combo)

        self._divider(parent)

        # ── Output path ─────────────────────────────────────────────────────
        self._section(parent, "📁  Save Location")
        path_frame = tk.Frame(parent, bg=self.BG)
        path_frame.pack(fill="x", padx=18)

        self._out_dir = tk.StringVar(value=_get_saved_location())
        path_entry = tk.Entry(path_frame, textvariable=self._out_dir,
                              font=self.FONT_SH, bg=self.INP_BG, fg=self.INP_FG,
                              relief="flat", bd=0, width=52,
                              highlightthickness=1, highlightbackground=self.BORDER,
                              highlightcolor=self.ACCENT)
        path_entry.pack(side="left", ipady=7, ipadx=6, pady=(4,0))
        tk.Button(path_frame, text="Browse", command=self._browse,
                  font=self.FONT_SH, bg=self.ACCENT, fg="white",
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=self.ACCENT2, activeforeground="white",
                  padx=12, pady=7).pack(side="left", padx=(8,0), pady=(4,0))

        # ── Generate button ──────────────────────────────────────────────────
        btn_frame = tk.Frame(parent, bg=self.BG)
        btn_frame.pack(fill="x", padx=18, pady=(20, 24))

        self._gen_btn = tk.Button(
            btn_frame, text="⬇  Generate PDF",
            font=("Segoe UI", 11, "bold"),
            bg=self.ACCENT, fg="white", activebackground=self.ACCENT2,
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=24, pady=12,
            command=self._generate
        )
        self._gen_btn.pack(fill="x")

        self._status_lbl = tk.Label(parent, text="", font=self.FONT_SH,
                                    bg=self.BG, fg=self.SUCCESS)
        self._status_lbl.pack(pady=(0, 8))

    # ── Widget helpers ───────────────────────────────────────────────────────

    def _toggle_btn(self, parent, text, value):
        btn = tk.Button(
            parent, text=text, font=self.FONT_B,
            relief="flat", bd=0, padx=18, pady=8, cursor="hand2",
            command=lambda: self._doc_type.set(value)
        )
        return btn

    def _refresh_toggle(self):
        active = self._doc_type.get()
        for btn, val in [(self._inv_btn, "invoice"), (self._rec_btn, "receipt")]:
            if val == active:
                btn.configure(bg=self.ACCENT, fg="white")
            else:
                btn.configure(bg=self.BORDER, fg=self.DARK)

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=self.BG)
        f.pack(fill="x", padx=18, pady=(14, 6))
        tk.Label(f, text=title, font=self.FONT_B, bg=self.BG, fg=self.DARK).pack(anchor="w")

    def _divider(self, parent):
        tk.Frame(parent, bg=self.BORDER, height=1).pack(fill="x", padx=18, pady=(14, 0))

    def _field(self, parent, label, row=0, col=0, multiline=False,
               placeholder="", colspan=1):
        cell = tk.Frame(parent, bg=self.BG)
        cell.grid(row=row, column=col, columnspan=colspan,
                  sticky="nsew", padx=(0, 12 if col == 0 else 0), pady=(0, 10))
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        tk.Label(cell, text=label, font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).pack(anchor="w")

        if multiline:
            w = tk.Text(cell, height=3, font=self.FONT, bg=self.INP_BG,
                        fg=self.INP_FG, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=self.BORDER,
                        highlightcolor=self.ACCENT, padx=8, pady=6, wrap="word")
            if placeholder:
                w.insert("1.0", placeholder)
            w.pack(fill="x", pady=(3,0))
        else:
            w = tk.Entry(cell, font=self.FONT, bg=self.INP_BG, fg=self.INP_FG,
                         relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=self.BORDER,
                         highlightcolor=self.ACCENT)
            w.pack(fill="x", ipady=7, ipadx=8, pady=(3,0))
            if placeholder:
                w.insert(0, placeholder)
        return w

    def _style_combo(self, combo):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=self.INP_BG,
                        background=self.INP_BG,
                        foreground=self.INP_FG,
                        bordercolor=self.BORDER,
                        arrowcolor=self.MUTED,
                        padding=(8, 6))

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._out_dir.get())
        if d:
            self._out_dir.set(d)
            _save_location(d)

    def _update_total(self, _event=None):
        try:
            exc  = float(self._get(self.f_exc) or 0)
            rate = float(self._get(self.f_vat) or 20)
            total = exc * (1 + rate / 100)
            self._total_var.set(f"Total (Incl. VAT): £{total:.2f}")
        except ValueError:
            self._total_var.set("Total (Incl. VAT): —")

    def _default_number(self):
        date_str = ""
        try:
            date_str = self._get(self.f_date)
        except AttributeError:
            pass
        if not date_str:
            date_str = datetime.today().strftime("%d %B %Y")
        return _preview_doc_number(self._doc_type.get(), date_str)

    def _refresh_doc_number(self, *_):
        self._doc_num_var.set(self._default_number())

    def _get(self, widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        return widget.get().strip()

    # ── History helpers ─────────────────────────────────────────────────────

    def _refresh_history(self, *_):
        query       = self._hist_search.get().strip().lower() if hasattr(self, "_hist_search") else ""
        all_entries = _load_history()
        total       = len(all_entries)

        # Update header to show count + warn if near limit
        if total >= WARN_HISTORY:
            badge = f"  ⚠️ {total}/{MAX_HISTORY}"
            self._hist_count_lbl.configure(fg="#FCD34D")
        else:
            badge = f"  ({total})"
            self._hist_count_lbl.configure(fg="white")
        self._hist_count_lbl.configure(text=f"🕐  Document History{badge}")

        filtered = [
            e for e in all_entries
            if query in e.get("client_name", "").lower()
            or query in e.get("number", "").lower()
            or query in e.get("doc_type", "").lower()
            or query in e.get("description", "").lower()
        ] if query else all_entries

        self._hist_lb.delete(0, "end")
        for e in filtered:
            dt   = "INV" if e.get("doc_type") == "invoice" else "REC"
            num  = e.get("number", "—")
            name = e.get("client_name", "—")
            gen  = e.get("generated_at", "")[:10]
            total_str = ""
            try:
                total_str = f"  £{float(e.get('amount_exc',0)) * (1 + float(e.get('vat_rate', 20)) / 100):.2f}"
            except Exception:
                pass
            link = ""
            if e.get("receipt_number"):
                link = f"  ✔ Paid → {e['receipt_number']}"
            elif e.get("from_invoice"):
                link = f"  (for {e['from_invoice']})"
            label = f"[{dt}] {num:<18} {name:<26} {gen}{total_str}{link}"
            self._hist_lb.insert("end", label)
        self._history_filtered = filtered

    def _export_history(self):
        """Export all history, or only the rows matching the current search, to CSV."""
        query   = self._hist_search.get().strip()
        entries = self._history_filtered if query else _load_history()
        if not entries:
            messagebox.showinfo("Nothing to Export", "There are no history records to export.")
            return

        scope = f"{len(entries)} record(s) matching \"{query}\"" if query else f"all {len(entries)} record(s)"
        default_name = f"billing_history_{datetime.today().strftime('%Y-%m-%d')}.csv"
        out_path = filedialog.asksaveasfilename(
            title=f"Export {scope}",
            initialdir=self._out_dir.get() if os.path.isdir(self._out_dir.get()) else _get_saved_location(),
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV (opens in Excel)", "*.csv"), ("All files", "*.*")],
        )
        if not out_path:
            return

        try:
            export_history_csv(entries, out_path)
        except PermissionError:
            messagebox.showerror("Export Failed",
                                 "Could not write the file. If it is open in Excel, close it and try again.")
            return
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export history:\n{e}")
            return

        self._status_lbl.configure(text=f"✅  Exported {scope} to: {out_path}", fg=self.SUCCESS)
        if messagebox.askyesno("Export Complete", f"Exported {scope} to:\n{out_path}\n\nOpen it now?"):
            import subprocess, platform
            if platform.system() == "Windows":
                os.startfile(out_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", out_path])
            else:
                subprocess.run(["xdg-open", out_path])

    def _invoice_to_receipt(self):
        """Mark the selected invoice as paid and create its receipt with a new receipt number."""
        import re
        sel = self._hist_lb.curselection()
        if not sel:
            messagebox.showinfo("Select an Invoice",
                                "Click an invoice in the history list first, then choose Mark Paid.")
            return
        inv = self._history_filtered[sel[0]]

        if inv.get("doc_type") != "invoice":
            messagebox.showinfo("Not an Invoice",
                                "This record is already a receipt. Select an invoice instead.")
            return

        try:
            exc   = float(inv.get("amount_exc", 0))
            rate  = float(inv.get("vat_rate", 20))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Amount",
                                 "This invoice has an unreadable amount. Load it into the form and generate the receipt manually.")
            return
        total = exc * (1 + rate / 100)

        if inv.get("receipt_number"):
            if not messagebox.askyesno(
                    "Already Receipted",
                    f"Invoice {inv.get('number')} already has receipt {inv['receipt_number']}.\n\n"
                    "Create another receipt for it anyway?"):
                return
        elif not messagebox.askyesno(
                "Mark Paid and Create Receipt",
                f"Invoice:  {inv.get('number')}\n"
                f"Client:   {inv.get('client_name', '')}\n"
                f"Total:    £{total:.2f}\n\n"
                "Mark this invoice as Paid and create a receipt dated today?"):
            return

        _day_fmt  = "%#d" if sys.platform == "win32" else "%-d"
        today_str = datetime.today().strftime(f"{_day_fmt} %B %Y")
        rec_number = _get_next_doc_number("receipt", today_str)

        data = {
            "client_name":    inv.get("client_name", ""),
            "client_address": inv.get("client_address", ""),
            "client_phone":   inv.get("client_phone", ""),
            "client_email":   inv.get("client_email", ""),
            "date":           today_str,
            "number":         rec_number,
            "description":    inv.get("description", ""),
            "course_date":    inv.get("course_date", ""),
            "amount_exc":     inv.get("amount_exc", ""),
            "vat_rate":       inv.get("vat_rate", "20"),
            "status":         "Paid",
            "doc_type":       "receipt",
        }

        out_dir = self._out_dir.get()
        if not os.path.isdir(out_dir):
            out_dir = _get_saved_location()
        out_path  = _pdf_path(out_dir, "receipt", rec_number, data["client_name"])

        try:
            generate_receipt(data, out_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt:\n{e}")
            return

        _save_history_entry({
            "number":         rec_number,
            "doc_type":       "receipt",
            "date":           today_str,
            "client_name":    data["client_name"],
            "client_address": data["client_address"],
            "client_phone":   data["client_phone"],
            "client_email":   data["client_email"],
            "description":    data["description"],
            "course_date":    data["course_date"],
            "amount_exc":     data["amount_exc"],
            "vat_rate":       data["vat_rate"],
            "status":         "Paid",
            "from_invoice":   inv.get("number", ""),
            "generated_at":   datetime.today().isoformat(timespec="seconds"),
        })
        _update_history_entry(inv, {
            "status":         "Paid",
            "receipt_number": rec_number,
            "paid_on":        today_str,
        })

        self._refresh_doc_number()
        self._refresh_history()
        self._status_lbl.configure(
            text=f"✅  {inv.get('number')} marked Paid. Receipt {rec_number} saved: {out_path}",
            fg=self.SUCCESS)

        if messagebox.askyesno("Receipt Created",
                               f"Receipt {rec_number} saved to:\n{out_path}\n\nOpen it now?"):
            import subprocess, platform
            if platform.system() == "Windows":
                os.startfile(out_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", out_path])
            else:
                subprocess.run(["xdg-open", out_path])

    def _load_from_history(self, event=None):
        sel = self._hist_lb.curselection()
        if not sel:
            return
        entry = self._history_filtered[sel[0]]

        self._doc_type.set(entry.get("doc_type", "invoice"))

        def _set(widget, val):
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
                widget.insert("1.0", val)
            else:
                widget.delete(0, "end")
                widget.insert(0, val)

        _set(self.f_name,    entry.get("client_name", ""))
        _set(self.f_address, entry.get("client_address", ""))
        _set(self.f_phone,   entry.get("client_phone", ""))
        _set(self.f_email,   entry.get("client_email", ""))
        _set(self.f_desc,    entry.get("description", ""))
        _set(self.f_cdate,   entry.get("course_date", ""))
        _set(self.f_exc,     entry.get("amount_exc", ""))
        _set(self.f_vat,     entry.get("vat_rate", "20"))

        _day_fmt = "%#d" if sys.platform == "win32" else "%-d"
        _set(self.f_date, datetime.today().strftime(f"{_day_fmt} %B %Y"))

        self._status_var.set(entry.get("status", "Payment Outstanding"))
        self._course_var.set("— select a course —")
        self._update_total()
        self._refresh_doc_number()
        self._status_lbl.configure(
            text=f"✏️  Loaded: {entry.get('client_name', '')} — review then Generate",
            fg=self.DARK
        )

    # ── Course library helpers ────────────────────────────────────────────────

    def _refresh_course_combo(self):
        courses = _load_courses()
        names   = [c["name"] for c in courses] + ["＋ Add new course…"]
        self._course_combo["values"] = names

    def _on_course_selected(self, event=None):
        val = self._course_var.get()
        if val == "＋ Add new course…":
            self._course_var.set("— select a course —")
            self._open_course_manager()
            return
        match = next((c for c in _load_courses() if c["name"] == val), None)
        if not match:
            return
        self.f_desc.delete("1.0", "end")
        self.f_desc.insert("1.0", match["name"])
        rate = float(match.get("vat_rate", 20))
        exc  = float(match["price_inc"]) / (1 + rate / 100)
        self.f_exc.delete(0, "end"); self.f_exc.insert(0, f"{exc:.2f}")
        self.f_vat.delete(0, "end"); self.f_vat.insert(0, str(int(rate)))
        self._update_total()

    def _open_course_manager(self):
        win = tk.Toplevel(self)
        win.title("Course Library")
        win.geometry("700x520")
        win.configure(bg=self.BG)
        win.grab_set()

        tk.Label(win, text="Course Library", font=("Segoe UI", 13, "bold"),
                 bg=self.BG, fg=self.DARK).pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(win, text="Double-click a row to edit. Prices are inclusive of VAT.",
                 font=self.FONT_SH, bg=self.BG, fg=self.MUTED).pack(anchor="w", padx=18, pady=(0, 8))

        cols = ("name", "price_inc", "vat_rate")
        tree_frame = tk.Frame(win, bg=self.BG)
        tree_frame.pack(fill="both", expand=True, padx=18)

        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
        tree.heading("name",      text="Course Name")
        tree.heading("price_inc", text="Price (incl. VAT) £")
        tree.heading("vat_rate",  text="VAT %")
        tree.column("name",      width=420, anchor="w")
        tree.column("price_inc", width=130, anchor="center")
        tree.column("vat_rate",  width=70,  anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        def _reload_tree():
            tree.delete(*tree.get_children())
            for c in _load_courses():
                tree.insert("", "end", values=(c["name"], f"{c['price_inc']:.2f}", c.get("vat_rate", 20)))

        _reload_tree()

        form = tk.Frame(win, bg=self.BG)
        form.pack(fill="x", padx=18, pady=(10, 4))

        tk.Label(form, text="Course Name:", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).grid(row=0, column=0, sticky="w")
        e_name = tk.Entry(form, font=self.FONT, bg=self.INP_BG, fg=self.INP_FG,
                          relief="flat", bd=0,
                          highlightthickness=1, highlightbackground=self.BORDER, width=44)
        e_name.grid(row=0, column=1, padx=(8, 16), ipady=5, ipadx=6, sticky="ew")

        tk.Label(form, text="Price (incl. VAT) £:", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).grid(row=0, column=2, sticky="w")
        e_price = tk.Entry(form, font=self.FONT, bg=self.INP_BG, fg=self.INP_FG,
                           relief="flat", bd=0,
                           highlightthickness=1, highlightbackground=self.BORDER, width=8)
        e_price.grid(row=0, column=3, padx=(8, 16), ipady=5, ipadx=6)

        tk.Label(form, text="VAT %:", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).grid(row=0, column=4, sticky="w")
        e_vat = tk.Entry(form, font=self.FONT, bg=self.INP_BG, fg=self.INP_FG,
                         relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=self.BORDER, width=5)
        e_vat.insert(0, "20")
        e_vat.grid(row=0, column=5, padx=(8, 0), ipady=5, ipadx=6)

        editing_index = [None]

        def _on_double_click(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])["values"]
            e_name.delete(0, "end");  e_name.insert(0, vals[0])
            e_price.delete(0, "end"); e_price.insert(0, vals[1])
            e_vat.delete(0, "end");   e_vat.insert(0, vals[2])
            courses = _load_courses()
            editing_index[0] = next(
                (i for i, c in enumerate(courses) if c["name"] == vals[0]), None)

        tree.bind("<Double-Button-1>", _on_double_click)

        btn_row = tk.Frame(win, bg=self.BG)
        btn_row.pack(fill="x", padx=18, pady=(4, 16))

        def _save_entry():
            name  = e_name.get().strip()
            price = e_price.get().strip()
            vat   = e_vat.get().strip()
            if not name or not price:
                messagebox.showerror("Missing", "Course name and price are required.", parent=win)
                return
            try:
                price_f = float(price); vat_f = float(vat)
            except ValueError:
                messagebox.showerror("Invalid", "Price and VAT must be numbers.", parent=win)
                return
            courses = _load_courses()
            entry   = {"name": name, "price_inc": price_f, "vat_rate": vat_f}
            if editing_index[0] is not None:
                courses[editing_index[0]] = entry
                editing_index[0] = None
            else:
                courses.append(entry)
            _save_courses(courses)
            _reload_tree()
            e_name.delete(0, "end"); e_price.delete(0, "end")
            e_vat.delete(0, "end"); e_vat.insert(0, "20")
            self._refresh_course_combo()

        def _delete_entry():
            sel = tree.selection()
            if not sel:
                return
            vals    = tree.item(sel[0])["values"]
            courses = [c for c in _load_courses() if c["name"] != vals[0]]
            _save_courses(courses)
            _reload_tree()
            self._refresh_course_combo()

        tk.Button(btn_row, text="💾  Save / Update", font=self.FONT_B,
                  bg=self.ACCENT, fg="white", relief="flat", bd=0,
                  cursor="hand2", padx=14, pady=7, command=_save_entry).pack(side="left")
        tk.Button(btn_row, text="🗑  Delete Selected", font=self.FONT_B,
                  bg="#FDECEA", fg=RED, relief="flat", bd=0,
                  cursor="hand2", padx=14, pady=7, command=_delete_entry).pack(side="left", padx=(10, 0))
        tk.Button(btn_row, text="✖  Close", font=self.FONT_B,
                  bg=self.BORDER, fg=self.DARK, relief="flat", bd=0,
                  cursor="hand2", padx=14, pady=7, command=win.destroy).pack(side="right")

    # ── Validation & generation ──────────────────────────────────────────────────

    def _validate(self):
        required = {
            "Client Name":        self.f_name,
            "Client Address":     self.f_address,
            "Client Phone":       self.f_phone,
            "Client Email":       self.f_email,
            "Date":               self.f_date,
            "Course Description": self.f_desc,
            "Course Date":        self.f_cdate,
            "Amount (Excl. VAT)": self.f_exc,
            "VAT Rate":           self.f_vat,
        }
        for name, widget in required.items():
            if not self._get(widget):
                messagebox.showerror("Missing Field", f"Please fill in: {name}")
                widget.focus()
                return False
        try:
            float(self._get(self.f_exc))
            float(self._get(self.f_vat))
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount and VAT Rate must be numbers.")
            return False
        return True

    def _generate(self):
        if not self._validate():
            return

        import re
        doc_type     = self._doc_type.get()
        date_entered = self._get(self.f_date)
        auto_number  = _get_next_doc_number(doc_type, date_entered)
        self._doc_num_var.set(auto_number)

        data = {
            "client_name":    self._get(self.f_name),
            "client_address": self._get(self.f_address),
            "client_phone":   self._get(self.f_phone),
            "client_email":   self._get(self.f_email),
            "date":           date_entered,
            "number":         auto_number,
            "description":    self._get(self.f_desc),
            "course_date":    self._get(self.f_cdate),
            "amount_exc":     self._get(self.f_exc),
            "vat_rate":       self._get(self.f_vat),
            "status":         self._status_var.get(),
            "doc_type":       doc_type,
        }

        out_path  = _pdf_path(self._out_dir.get(), doc_type, auto_number, data["client_name"])

        try:
            self._gen_btn.configure(text="⏳  Generating…", state="disabled")
            self.update()
            if doc_type == "invoice":
                generate_invoice(data, out_path)
            else:
                generate_receipt(data, out_path)

            self._gen_btn.configure(text="⬇  Generate PDF", state="normal")
            self._status_lbl.configure(text=f"✅  Saved: {out_path}", fg=self.SUCCESS)

            _save_location(self._out_dir.get())
            _save_history_entry({
                "number":         auto_number,
                "doc_type":       doc_type,
                "date":           data["date"],
                "client_name":    data["client_name"],
                "client_address": data["client_address"],
                "client_phone":   data["client_phone"],
                "client_email":   data["client_email"],
                "description":    data["description"],
                "course_date":    data["course_date"],
                "amount_exc":     data["amount_exc"],
                "vat_rate":       data["vat_rate"],
                "status":         data["status"],
                "generated_at":   datetime.today().isoformat(timespec="seconds"),
            })
            self._refresh_doc_number()
            self._refresh_history()

            # Warn if history is getting full
            total = len(_load_history())
            if total >= WARN_HISTORY:
                messagebox.showwarning(
                    "History Nearly Full",
                    f"You have {total} of {MAX_HISTORY} history entries saved.\nConsider exporting or clearing old records soon."
                )

            if messagebox.askyesno("Done!", f"PDF saved to:\n{out_path}\n\nOpen it now?"):
                import subprocess, platform
                if platform.system() == "Windows":
                    os.startfile(out_path)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", out_path])
                else:
                    subprocess.run(["xdg-open", out_path])
        except Exception as e:
            self._gen_btn.configure(text="⬇  Generate PDF", state="normal")
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")


if __name__ == "__main__":
    _backup_settings_daily()
    app = App()
    app.mainloop()
