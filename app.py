"""
First Aid Tutors — Invoice & Receipt Generator
Run: python app.py
Requires: pip install reportlab pillow customtkinter
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
#  GUI  (CustomTkinter)
# ─────────────────────────────────────────────────────────────────────────────

import customtkinter as ctk
from datetime import date, timedelta

ctk.set_appearance_mode("light")

OUTSTANDING_STATUSES = {"Payment Outstanding", "Partially Paid", "Awaiting Bank Transfer"}
PAYMENT_STATUSES     = ["Payment Outstanding", "Paid", "Partially Paid",
                        "Awaiting Bank Transfer", "Refunded"]
COURSE_PLACEHOLDER   = "Select a course from the library"
DATE_FORMATS         = ["%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d",
                        "%d %B %Y", "%d %b %Y", "%B %d %Y"]


def _today_str() -> str:
    _day_fmt = "%#d" if sys.platform == "win32" else "%-d"
    return datetime.today().strftime(f"{_day_fmt} %B %Y")


def _parse_user_date(text: str):
    """Strict date parse for user input. Returns a date, or None if unreadable."""
    text = (text or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _entry_date(entry: dict):
    """The date a history record belongs to: its document date, else when it was generated."""
    d = _parse_user_date(entry.get("date", ""))
    if d:
        return d
    try:
        return datetime.fromisoformat(entry.get("generated_at", "")).date()
    except (TypeError, ValueError):
        return None


def _entry_total(entry: dict) -> float:
    total = _vat_parts(entry)[1]
    return total if isinstance(total, float) else 0.0


def _is_outstanding(entry: dict) -> bool:
    return (entry.get("doc_type") == "invoice"
            and not entry.get("receipt_number")
            and entry.get("status", "Payment Outstanding") in OUTSTANDING_STATUSES)


def _open_file(path: str):
    import subprocess, platform
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])


class StatusLabel(ctk.CTkLabel):
    """A CTkLabel that also accepts tk-style fg= colour arguments."""
    def configure(self, require_redraw=False, **kwargs):
        if "fg" in kwargs:
            kwargs["text_color"] = kwargs.pop("fg")
        super().configure(require_redraw=require_redraw, **kwargs)


class MultiText(ctk.CTkTextbox):
    """A CTkTextbox that also accepts Entry-style indexes (0), so older helper
    code can fill it the same way as a one-line field."""
    @staticmethod
    def _idx(index):
        return "1.0" if index in (0, "0") else index

    def delete(self, index1, index2=None):
        super().delete(self._idx(index1), index2)

    def insert(self, index, text, tags=None):
        super().insert(self._idx(index), text, tags)

    def value(self) -> str:
        return self.get("1.0", "end").strip()


class App(ctk.CTk):
    # ── colour palette ──────────────────────────────────────────────────────
    BG       = "#F4F5F7"
    PANEL    = "#FFFFFF"
    ACCENT   = "#C0392B"
    ACCENT2  = "#A93226"
    DARK     = "#1A1A2E"
    DARK2    = "#2A2A44"
    MUTED    = "#5B6270"
    BORDER   = "#E3E5E9"
    FIELD_BD = "#D5D8DE"
    SUCCESS  = "#166534"
    SUCCESS2 = "#14532D"
    WARN     = "#92400E"
    INP_BG   = "#FFFFFF"
    INP_FG   = "#1A1A2E"
    FAMILY   = "Segoe UI"

    PILL = {
        "Paid":        ("#DCFCE7", "#166534"),
        "Outstanding": ("#FEF3C7", "#92400E"),
        "Other":       ("#EEF0F3", "#3D4350"),
    }

    def __init__(self):
        super().__init__()
        self.title("First Aid Tutors — Billing")
        self.configure(fg_color=self.BG)
        try:
            ico = resource_path("logo.ico")
            if os.path.exists(ico) and sys.platform == "win32":
                self.iconbitmap(ico)
        except Exception:
            pass

        # fonts
        f = self.FAMILY
        self.F_XS   = ctk.CTkFont(family=f, size=11)
        self.F_SM   = ctk.CTkFont(family=f, size=12)
        self.F      = ctk.CTkFont(family=f, size=13)
        self.F_B    = ctk.CTkFont(family=f, size=13, weight="bold")
        self.F_H2   = ctk.CTkFont(family=f, size=15, weight="bold")
        self.F_H1   = ctk.CTkFont(family=f, size=22, weight="bold")
        self.F_BIG  = ctk.CTkFont(family=f, size=22, weight="bold")
        self.F_TILE = ctk.CTkFont(family=f, size=21, weight="bold")

        # state
        self._doc_type        = tk.StringVar(value="invoice")
        self._doc_num_var     = tk.StringVar(value="")
        self._doc_num_lbl_var = tk.StringVar(value="INVOICE NUMBER")
        self._sub_var         = tk.StringVar(value="£0.00")
        self._vat_lbl_var     = tk.StringVar(value="VAT (20%)")
        self._vat_var         = tk.StringVar(value="£0.00")
        self._total_var       = tk.StringVar(value="£0.00")
        self._status_var      = tk.StringVar(value="Payment Outstanding")
        self._course_var      = tk.StringVar(value=COURSE_PLACEHOLDER)
        self._out_dir         = tk.StringVar(value=_get_saved_location())
        self._hist_filter     = tk.StringVar(value="All")
        self._history_all      = []
        self._history_filtered = []

        self._resp       = {}      # card grids that reflow to one column when narrow
        self._layout_key = None
        self._nav_btns   = {}      # key -> list of nav buttons (sidebar and top bar)

        self._size_window()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_sidebar()
        self._build_topbar()
        self._content = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=0)
        self._content.grid(row=1, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._page_new  = self._build_new_page(self._content)
        self._page_hist = self._build_history_page(self._content)
        for p in (self._page_new, self._page_hist):
            p.grid(row=0, column=0, sticky="nsew")

        self._doc_type.trace_add("write", self._on_doc_type_changed)
        self._on_doc_type_changed()
        self._refresh_history()
        self._show_page("new")
        self._apply_layout()
        self.bind("<Configure>", self._on_resize, add="+")

    # ── Window and navigation ────────────────────────────────────────────────

    def _size_window(self):
        try:
            scale = ctk.ScalingTracker.get_window_scaling(self)
        except Exception:
            scale = 1.0
        sw = self.winfo_screenwidth() / scale
        sh = self.winfo_screenheight() / scale
        w = int(min(1280, sw - 60))
        h = int(min(820, sh - 90))
        self.geometry(f"{w}x{h}+{max(int((sw - w) / 2), 0)}+{max(int((sh - h) / 3), 0)}")
        self.minsize(min(720, w), min(560, h))

    def _show_page(self, name):
        self._current_page = name
        page = self._page_new if name == "new" else self._page_hist
        page.tkraise()
        for key, btns in self._nav_btns.items():
            active = key == name
            for btn in btns:
                btn.configure(fg_color=self.DARK2 if active else "transparent",
                              text_color="#FFFFFF" if active else "#C9CED8")
        if name == "hist":
            self._refresh_history()

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, width=232, fg_color=self.DARK, corner_radius=0)
        bar.grid(row=1, column=0, sticky="nsw")
        self._sidebar = bar
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_rowconfigure(10, weight=1)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 28))
        mark = ctk.CTkLabel(brand, text="+", width=40, height=40, corner_radius=10,
                            fg_color=self.ACCENT, text_color="#FFFFFF",
                            font=ctk.CTkFont(family=self.FAMILY, size=24, weight="bold"))
        mark.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(brand, text="First Aid Tutors", text_color="#FFFFFF",
                     font=ctk.CTkFont(family=self.FAMILY, size=15, weight="bold"),
                     anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(brand, text="Billing", text_color="#A5ACBA", font=self.F_SM,
                     anchor="w", height=16).grid(row=1, column=1, sticky="w")


        def nav(row, key, text, command):
            b = ctk.CTkButton(bar, text=text, anchor="w", height=42, corner_radius=8,
                              font=self.F_B if key else self.F, fg_color="transparent",
                              hover_color=self.DARK2, text_color="#C9CED8",
                              command=command)
            b.grid(row=row, column=0, sticky="ew", padx=14, pady=2)
            if key:
                self._nav_btns.setdefault(key, []).append(b)
            return b

        nav(1, "new",  "     New document", lambda: self._show_page("new"))
        self._nav_hist_btn = nav(2, "hist", "     History", lambda: self._show_page("hist"))
        nav(3, None,   "     Course library", self._open_course_manager)

        box = ctk.CTkFrame(bar, fg_color="#24243A", corner_radius=10)
        box.grid(row=11, column=0, sticky="ew", padx=14, pady=20)
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(box, text="History storage", text_color="#A5ACBA", font=self.F_XS,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        self._store_bar = ctk.CTkProgressBar(box, height=6, corner_radius=3,
                                             fg_color="#3A3A55", progress_color="#4ADE80")
        self._store_bar.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        self._store_lbl = ctk.CTkLabel(box, text="", text_color="#C9CED8", font=self.F_XS,
                                       anchor="w")
        self._store_lbl.grid(row=2, column=0, sticky="w", padx=14)
        backed_up = os.path.exists(os.path.join(
            BACKUP_DIR, f"fat_generator_settings_{datetime.today().strftime('%Y-%m-%d')}.json"))
        ctk.CTkLabel(box, text="Backed up today" if backed_up else "Backup runs at start-up",
                     text_color="#4ADE80" if backed_up else "#A5ACBA", font=self.F_XS,
                     anchor="w").grid(row=3, column=0, sticky="w", padx=14, pady=(0, 12))

    def _build_topbar(self):
        """Compact navigation shown instead of the sidebar when the window is narrow."""
        top = ctk.CTkFrame(self, height=56, fg_color=self.DARK, corner_radius=0)
        self._topbar = top
        ctk.CTkLabel(top, text="+", width=32, height=32, corner_radius=8,
                     fg_color=self.ACCENT, text_color="#FFFFFF",
                     font=ctk.CTkFont(family=self.FAMILY, size=19, weight="bold")
                     ).pack(side="left", padx=(14, 8), pady=12)
        ctk.CTkLabel(top, text="First Aid Tutors", text_color="#FFFFFF",
                     font=self.F_B).pack(side="left", padx=(0, 14))
        for key, text, cmd in (("new", "New document", lambda: self._show_page("new")),
                               ("hist", "History", lambda: self._show_page("hist")),
                               (None, "Courses", self._open_course_manager)):
            b = ctk.CTkButton(top, text=text, width=10, height=34, corner_radius=8,
                              font=self.F_B if key else self.F, fg_color="transparent",
                              hover_color=self.DARK2, text_color="#C9CED8", command=cmd)
            b.pack(side="left", padx=2)
            if key:
                self._nav_btns.setdefault(key, []).append(b)
        self._top_store_lbl = ctk.CTkLabel(top, text="", text_color="#A5ACBA", font=self.F_XS)
        self._top_store_lbl.pack(side="right", padx=14)

    # ── Responsive layout ────────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget is not self:
            return
        if getattr(self, "_resize_job", None):
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(60, self._apply_layout)

    def _apply_layout(self):
        """Reflow the screens to fit the window, e.g. when snapped to half the screen."""
        self._resize_job = None
        try:
            scale = ctk.ScalingTracker.get_window_scaling(self)
        except Exception:
            scale = 1.0
        width = self.winfo_width() / scale
        if width < 50:
            return
        compact_nav  = width < 1000
        content_w    = width - (0 if compact_nav else 232)
        summary_w    = 340 if content_w >= 1000 else 290
        single_col   = content_w - summary_w - 72 < 600
        hist_narrow  = content_w < 940
        key = (compact_nav, summary_w, single_col, hist_narrow)
        if key == self._layout_key:
            return
        self._layout_key = key

        # navigation
        if compact_nav:
            self._sidebar.grid_remove()
            self._topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        else:
            self._topbar.grid_remove()
            self._sidebar.grid()

        # new document page
        self._summary.configure(width=summary_w)
        self._status_lbl.configure(wraplength=summary_w - 50)
        for frame, info in self._resp.items():
            for i, (cell, row, col, span) in enumerate(info["items"]):
                if single_col:
                    cell.grid_configure(row=i, column=0, columnspan=info["ncols"])
                else:
                    cell.grid_configure(row=row, column=col, columnspan=span)

        # history page
        for i, t in enumerate(self._tile_cards):
            if hist_narrow:
                t.grid_configure(row=i // 2, column=i % 2, pady=(0, 12) if i < 2 else 0)
            else:
                t.grid_configure(row=0, column=i, pady=0)
        self._tiles_frame.grid_columnconfigure((2, 3), weight=0 if hist_narrow else 1,
                                               uniform="" if hist_narrow else "tiles")
        if hist_narrow:
            self._hist_search.grid_configure(row=0, column=0, columnspan=3, pady=(0, 10))
            self._filter_seg.grid_configure(row=1, column=0, columnspan=1, sticky="w", padx=0)
            self._hist_count_lbl.grid_configure(row=1, column=2)
            self._tree.configure(displaycolumns=("type", "number", "client", "date",
                                                 "total", "status"))
            self._hist_hint.grid_remove()
        else:
            self._hist_search.grid_configure(row=0, column=0, columnspan=1, pady=0)
            self._filter_seg.grid_configure(row=0, column=1, columnspan=1, sticky="", padx=(12, 12))
            self._hist_count_lbl.grid_configure(row=0, column=2)
            self._tree.configure(displaycolumns="#all")
            self._hist_hint.grid()

    # ── Small widget helpers ─────────────────────────────────────────────────

    def _card(self, parent, **grid):
        c = ctk.CTkFrame(parent, fg_color=self.PANEL, corner_radius=12,
                         border_width=1, border_color=self.BORDER)
        c.grid(**grid)
        return c

    def _field(self, parent, label, row, col, colspan=1, multiline=False,
               height=56, placeholder=""):
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=8, pady=6)
        cell.grid_columnconfigure(0, weight=1)
        if parent in self._resp:
            self._resp[parent]["items"].append((cell, row, col, colspan))
        ctk.CTkLabel(cell, text=label, font=self.F_SM, text_color=self.MUTED, anchor="w",
                     height=18).grid(row=0, column=0, sticky="w", pady=(0, 4))
        if multiline:
            w = MultiText(cell, height=height, font=self.F, fg_color=self.INP_BG,
                          text_color=self.INP_FG, border_width=1,
                          border_color=self.FIELD_BD, corner_radius=8, wrap="word")
        else:
            w = ctk.CTkEntry(cell, height=38, font=self.F, fg_color=self.INP_BG,
                             text_color=self.INP_FG, border_width=1,
                             border_color=self.FIELD_BD, corner_radius=8,
                             placeholder_text=placeholder)
        w.grid(row=1, column=0, sticky="ew")
        return w

    def _option(self, parent, variable, values, command=None, width=200):
        return ctk.CTkOptionMenu(parent, variable=variable, values=values, command=command,
                                 height=38, width=width, corner_radius=8, font=self.F,
                                 dropdown_font=self.F, fg_color=self.INP_BG,
                                 button_color="#EEF0F3", button_hover_color="#E2E5EA",
                                 text_color=self.INP_FG, dynamic_resizing=False)

    def _primary(self, parent, text, command, height=40, color=None, hover=None):
        return ctk.CTkButton(parent, text=text, command=command, height=height,
                             corner_radius=10, font=self.F_B,
                             fg_color=color or self.ACCENT,
                             hover_color=hover or self.ACCENT2, text_color="#FFFFFF",
                             text_color_disabled="#F3D6D2" if not color else "#C9E4D2")

    def _secondary(self, parent, text, command, height=40):
        return ctk.CTkButton(parent, text=text, command=command, height=height,
                             corner_radius=10, font=self.F, fg_color=self.PANEL,
                             hover_color="#F1F2F5", text_color=self.DARK,
                             text_color_disabled="#A9AEB8",
                             border_width=1, border_color=self.FIELD_BD)

    def _pill(self, parent, status):
        key = ("Paid" if status == "Paid"
               else "Outstanding" if status in OUTSTANDING_STATUSES else "Other")
        bg, fg = self.PILL[key]
        text = "Outstanding" if status == "Payment Outstanding" else status
        return ctk.CTkLabel(parent, text=text, fg_color=bg, text_color=fg,
                            corner_radius=10, height=24, font=self.F_XS, padx=10)

    def _get(self, widget):
        if isinstance(widget, ctk.CTkTextbox):
            return widget.get("1.0", "end").strip()
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        return widget.get().strip()

    def _set(self, widget, value):
        value = "" if value is None else str(value)
        if isinstance(widget, (ctk.CTkTextbox, tk.Text)):
            widget.delete("1.0", "end")
            widget.insert("1.0", value)
        else:
            widget.delete(0, "end")
            if value:
                widget.insert(0, value)

    def _set_status(self, text, color=None):
        self._status_lbl.configure(text=text, text_color=color or self.SUCCESS)

    # ── New document page (layout A) ─────────────────────────────────────────

    def _build_new_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color=self.BG, corner_radius=0)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=32, pady=(26, 14))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="New document", font=self.F_H1, text_color=self.DARK,
                     anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(head, text="Fill in the details and generate a branded PDF.",
                     font=self.F, text_color=self.MUTED, anchor="w").grid(row=1, column=0, sticky="w")
        self._type_seg = ctk.CTkSegmentedButton(
            head, values=["Invoice", "Receipt"], height=40, font=self.F_B,
            corner_radius=10, fg_color="#E6E8EC", selected_color="#FFFFFF",
            selected_hover_color="#F7F7F9", unselected_color="#E6E8EC",
            unselected_hover_color="#DADDE3", text_color=self.DARK,
            command=lambda v: self._doc_type.set(v.lower()))
        self._type_seg.grid(row=0, column=1, rowspan=2, sticky="e")
        self._type_seg.set("Invoice")

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=(24, 32), pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(body, fg_color="transparent", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.grid_columnconfigure(0, weight=1)

        # Client card
        c1 = self._card(left, row=0, column=0, sticky="ew", padx=(8, 4), pady=(0, 14))
        c1.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(c1, text="Client", font=self.F_H2, text_color=self.DARK, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 2))
        inner1 = ctk.CTkFrame(c1, fg_color="transparent")
        inner1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 14))
        inner1.grid_columnconfigure((0, 1), weight=1, uniform="c1")
        self._resp[inner1] = {"ncols": 2, "items": []}
        self.f_name    = self._field(inner1, "Full name *", 0, 0)
        self.f_email   = self._field(inner1, "Email *", 0, 1)
        self.f_phone   = self._field(inner1, "Phone *", 1, 0)
        self.f_address = self._field(inner1, "Address *", 2, 0, colspan=2,
                                     multiline=True, height=60)

        # Course card
        c2 = self._card(left, row=1, column=0, sticky="ew", padx=(8, 4), pady=(0, 14))
        c2.grid_columnconfigure(0, weight=1)
        top2 = ctk.CTkFrame(c2, fg_color="transparent")
        top2.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 0))
        top2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top2, text="Course", font=self.F_H2, text_color=self.DARK, anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(top2, text="Manage courses", width=10, height=30, fg_color="transparent",
                      hover_color="#FBEAE8", text_color=self.ACCENT, font=self.F_B,
                      command=self._open_course_manager).grid(row=0, column=1, sticky="e")
        inner2 = ctk.CTkFrame(c2, fg_color="transparent")
        inner2.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 14))
        inner2.grid_columnconfigure((0, 1, 2), weight=1, uniform="c2")
        self._resp[inner2] = {"ncols": 3, "items": []}
        lib = ctk.CTkFrame(inner2, fg_color="transparent")
        lib.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=6)
        self._resp[inner2]["items"].append((lib, 0, 0, 3))
        lib.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lib, text="From course library", font=self.F_SM, text_color=self.MUTED,
                     anchor="w", height=18).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._course_combo = self._option(lib, self._course_var, [COURSE_PLACEHOLDER],
                                          command=self._on_course_selected)
        self._course_combo.grid(row=1, column=0, sticky="ew")
        self.f_desc  = self._field(inner2, "Course description *", 1, 0, colspan=3,
                                   multiline=True, height=52)
        self.f_cdate = self._field(inner2, "Course date *", 2, 0, placeholder="e.g. 5 November 2026")
        self.f_exc   = self._field(inner2, "Amount exc. VAT (£) *", 2, 1, placeholder="0.00")
        self.f_vat   = self._field(inner2, "VAT rate (%) *", 2, 2)
        self._set(self.f_vat, "20")
        for w in (self.f_exc, self.f_vat):
            w.bind("<KeyRelease>", self._update_total)
        self._refresh_course_combo()

        # Recent card
        c3 = self._card(left, row=2, column=0, sticky="ew", padx=(8, 4), pady=(0, 4))
        c3.grid_columnconfigure(0, weight=1)
        top3 = ctk.CTkFrame(c3, fg_color="transparent")
        top3.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 4))
        top3.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top3, text="Recent documents", font=self.F_H2, text_color=self.DARK,
                     anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(top3, text="View all", width=10, height=30, fg_color="transparent",
                      hover_color="#FBEAE8", text_color=self.ACCENT, font=self.F_B,
                      command=lambda: self._show_page("hist")).grid(row=0, column=1, sticky="e")
        self._recent_box = ctk.CTkFrame(c3, fg_color="transparent")
        self._recent_box.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))
        self._recent_box.grid_columnconfigure(1, weight=1)

        # Summary panel
        s = self._card(body, row=0, column=1, sticky="ns")
        s.configure(width=340)
        self._summary = s
        s.grid_propagate(False)
        s.grid_columnconfigure(0, weight=1)
        s.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(s, textvariable=self._doc_num_lbl_var, font=ctk.CTkFont(
            family=self.FAMILY, size=11, weight="bold"), text_color=self.MUTED, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 0))
        ctk.CTkLabel(s, textvariable=self._doc_num_var, font=self.F_BIG,
                     text_color=self.ACCENT, anchor="w").grid(row=1, column=0, sticky="w", padx=22)
        datebox = ctk.CTkFrame(s, fg_color="transparent")
        datebox.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 0))
        datebox.grid_columnconfigure(0, weight=1)
        self.f_date = self._field(datebox, "Document date *", 0, 0)
        self._set(self.f_date, _today_str())
        self.f_date.bind("<KeyRelease>", self._refresh_doc_number)
        self.f_date.bind("<FocusOut>",   self._refresh_doc_number)

        totals = ctk.CTkFrame(s, fg_color="#F8F9FA", corner_radius=10)
        totals.grid(row=3, column=0, sticky="ew", padx=22, pady=(10, 6))
        totals.grid_columnconfigure(0, weight=1)
        for r, (lbl_var, val_var) in enumerate([(None, self._sub_var),
                                                (self._vat_lbl_var, self._vat_var)]):
            ctk.CTkLabel(totals, text="Subtotal" if lbl_var is None else "",
                         textvariable=lbl_var, font=self.F, text_color=self.MUTED,
                         anchor="w").grid(row=r, column=0, sticky="w", padx=14,
                                          pady=(10 if r == 0 else 0, 0))
            ctk.CTkLabel(totals, textvariable=val_var, font=self.F, text_color=self.DARK,
                         anchor="e").grid(row=r, column=1, sticky="e", padx=14,
                                          pady=(10 if r == 0 else 0, 0))
        ctk.CTkFrame(totals, height=1, fg_color=self.BORDER).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=6)
        ctk.CTkLabel(totals, text="Total", font=ctk.CTkFont(family=self.FAMILY, size=17,
                     weight="bold"), text_color=self.DARK, anchor="w"
                     ).grid(row=3, column=0, sticky="w", padx=14, pady=(0, 10))
        ctk.CTkLabel(totals, textvariable=self._total_var, font=ctk.CTkFont(
            family=self.FAMILY, size=17, weight="bold"), text_color=self.DARK, anchor="e"
                     ).grid(row=3, column=1, sticky="e", padx=14, pady=(0, 10))

        st = ctk.CTkFrame(s, fg_color="transparent")
        st.grid(row=4, column=0, sticky="ew", padx=22, pady=(6, 0))
        st.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(st, text="Payment status", font=self.F_SM, text_color=self.MUTED,
                     anchor="w", height=18).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._option(st, self._status_var, PAYMENT_STATUSES).grid(row=1, column=0, sticky="ew")

        sv = ctk.CTkFrame(s, fg_color="transparent")
        sv.grid(row=5, column=0, sticky="ew", padx=22, pady=(12, 0))
        sv.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(sv, text="Save PDFs to", font=self.F_SM, text_color=self.MUTED,
                     anchor="w", height=18).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ctk.CTkEntry(sv, textvariable=self._out_dir, height=38, font=self.F_SM,
                     fg_color=self.INP_BG, text_color=self.INP_FG, border_width=1,
                     border_color=self.FIELD_BD, corner_radius=8).grid(row=1, column=0, sticky="ew")
        self._secondary(sv, "Browse", self._browse, height=38).grid(row=1, column=1, padx=(8, 0))
        sv.grid_columnconfigure(1, minsize=80)

        self._gen_btn = self._primary(s, "Generate invoice PDF", self._generate, height=50)
        self._gen_btn.grid(row=9, column=0, sticky="ew", padx=22, pady=(10, 8))
        self._secondary(s, "Clear form", self._clear_form, height=40).grid(
            row=10, column=0, sticky="ew", padx=22)
        self._status_lbl = StatusLabel(s, text="", font=self.F_SM, text_color=self.SUCCESS,
                                       wraplength=290, justify="left", anchor="w")
        self._status_lbl.grid(row=11, column=0, sticky="ew", padx=22, pady=(8, 16))

        self._update_total()
        return page

    def _render_recent(self):
        for w in self._recent_box.winfo_children():
            w.destroy()
        recent = self._history_all[:5]
        if not recent:
            ctk.CTkLabel(self._recent_box, text="No documents yet. Your history will appear here.",
                         font=self.F_SM, text_color=self.MUTED, anchor="w").grid(row=0, column=0, sticky="w")
            return
        for i, e in enumerate(recent):
            ctk.CTkFrame(self._recent_box, height=1, fg_color="#EEF0F3").grid(
                row=i * 2, column=0, columnspan=4, sticky="ew")
            r = i * 2 + 1
            ctk.CTkLabel(self._recent_box, text=e.get("number", ""), font=self.F_B,
                         text_color=self.DARK, anchor="w", width=130).grid(row=r, column=0, sticky="w", pady=6)
            ctk.CTkLabel(self._recent_box, text=e.get("client_name", ""), font=self.F,
                         text_color="#3D4350", anchor="w").grid(row=r, column=1, sticky="w", padx=8)
            ctk.CTkLabel(self._recent_box, text=f"£{_entry_total(e):,.2f}", font=self.F,
                         text_color=self.DARK, anchor="e", width=80).grid(row=r, column=2, sticky="e", padx=8)
            self._pill(self._recent_box, e.get("status", "")).grid(row=r, column=3, sticky="e")

    # ── History page (layout B) ──────────────────────────────────────────────

    def _build_history_page(self, parent):
        page = ctk.CTkFrame(parent, fg_color=self.BG, corner_radius=0)
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)

        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=32, pady=(26, 16))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="History", font=self.F_H1, text_color=self.DARK,
                     anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(head, text="Every invoice and receipt you have generated.",
                     font=self.F, text_color=self.MUTED, anchor="w").grid(row=1, column=0, sticky="w")
        self._secondary(head, "Export CSV", self._export_history).grid(
            row=0, column=1, rowspan=2, padx=(0, 10))
        self._primary(head, "+  New invoice", self._new_invoice).grid(row=0, column=2, rowspan=2)

        tiles = ctk.CTkFrame(page, fg_color="transparent")
        tiles.grid(row=1, column=0, sticky="ew", padx=24)
        tiles.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="tiles")
        self._tiles_frame = tiles
        self._tile_cards  = []
        self._tiles = []
        for i, label in enumerate(["Outstanding", "Received this month",
                                   "Documents this month", "History storage"]):
            t = self._card(tiles, row=0, column=i, sticky="ew", padx=8)
            self._tile_cards.append(t)
            t.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(t, text=label, font=self.F_SM, text_color=self.MUTED, anchor="w"
                         ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 0))
            v = ctk.CTkLabel(t, text="", font=self.F_TILE, text_color=self.DARK, anchor="w")
            v.grid(row=1, column=0, sticky="w", padx=18)
            n = ctk.CTkLabel(t, text="", font=self.F_XS, text_color=self.MUTED, anchor="w")
            n.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 14))
            self._tiles.append((v, n))

        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=32, pady=(18, 10))
        bar.grid_columnconfigure(0, weight=1)
        self._hist_search = ctk.CTkEntry(bar, height=38, font=self.F, corner_radius=10,
                                         fg_color=self.PANEL, border_width=1,
                                         border_color=self.FIELD_BD, text_color=self.INP_FG,
                                         placeholder_text="Search client, number or course")
        self._hist_search.grid(row=0, column=0, sticky="ew")
        self._hist_search.bind("<KeyRelease>", lambda *_: self._apply_history_filter())
        self._filter_seg = ctk.CTkSegmentedButton(
            bar, values=["All", "Outstanding", "Paid", "Receipts"], height=38, font=self.F,
            corner_radius=10, fg_color="#E6E8EC", selected_color="#FFFFFF",
            selected_hover_color="#F7F7F9", unselected_color="#E6E8EC",
            unselected_hover_color="#DADDE3", text_color=self.DARK,
            variable=self._hist_filter, command=lambda *_: self._apply_history_filter())
        self._filter_seg.grid(row=0, column=1, padx=(12, 12))
        self._hist_count_lbl = ctk.CTkLabel(bar, text="", font=self.F_SM, text_color=self.MUTED)
        self._hist_count_lbl.grid(row=0, column=2)

        table = self._card(page, row=3, column=0, sticky="nsew", padx=32, pady=(0, 10))
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(0, weight=1)
        self._style_tree()
        cols = ("type", "number", "client", "course", "date", "total", "status", "linked")
        heads = ("Type", "Number", "Client", "Course", "Date", "Total", "Status", "Linked document")
        widths = (70, 115, 160, 190, 95, 80, 105, 150)
        self._tree = ttk.Treeview(table, columns=cols, show="headings",
                                  style="Billing.Treeview", selectmode="browse")
        for c, h, w in zip(cols, heads, widths):
            self._tree.heading(c, text=h, anchor="e" if c == "total" else "w")
            self._tree.column(c, width=w, minwidth=60, anchor="e" if c == "total" else "w",
                              stretch=c in ("client", "course"))
        self._tree.tag_configure("outstanding", foreground=self.WARN)
        self._tree.tag_configure("odd", background="#FAFAFB")
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=2)
        sb = ctk.CTkScrollbar(table, command=self._tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 4))
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.bind("<Double-Button-1>", self._load_from_history)
        self._tree.bind("<Return>", self._load_from_history)
        self._tree.bind("<<TreeviewSelect>>", lambda *_: self._update_action_buttons())

        self._hist_menu = tk.Menu(self, tearoff=0)
        self._hist_menu.add_command(label="Mark paid and create receipt",
                                    command=self._invoice_to_receipt)
        self._hist_menu.add_command(label="Load into form", command=self._load_from_history)
        self._hist_menu.add_command(label="Open PDF", command=self._open_selected_pdf)

        def _on_right_click(event):
            row = self._tree.identify_row(event.y)
            if not row:
                return
            self._tree.selection_set(row)
            self._tree.focus(row)
            try:
                self._hist_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._hist_menu.grab_release()
        self._tree.bind("<Button-3>", _on_right_click)
        self._tree.bind("<Button-2>", _on_right_click)

        actions = ctk.CTkFrame(page, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=32, pady=(0, 22))
        self._pay_btn = self._primary(actions, "Mark paid → create receipt",
                                      self._invoice_to_receipt, color=self.SUCCESS,
                                      hover=self.SUCCESS2)
        self._pay_btn.grid(row=0, column=0)
        self._load_btn = self._secondary(actions, "Load into form", self._load_from_history)
        self._load_btn.grid(row=0, column=1, padx=10)
        self._pdf_btn = self._secondary(actions, "Open PDF", self._open_selected_pdf)
        self._pdf_btn.grid(row=0, column=2)
        self._hist_hint = ctk.CTkLabel(actions, text="Double-click a row to load it. Right-click for options.",
                                       font=self.F_SM, text_color=self.MUTED)
        self._hist_hint.grid(row=0, column=3, padx=16)
        return page

    def _style_tree(self):
        try:
            scale = ctk.ScalingTracker.get_widget_scaling(self)
        except Exception:
            scale = 1.0
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Billing.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=self.DARK, rowheight=int(36 * scale), borderwidth=0,
                        relief="flat", font=(self.FAMILY, 10))
        style.configure("Billing.Treeview.Heading", background="#F8F9FA", foreground=self.MUTED,
                        relief="flat", borderwidth=0, padding=(8, 8),
                        font=(self.FAMILY, 9, "bold"))
        style.map("Billing.Treeview.Heading", background=[("active", "#EEF0F3")])
        style.map("Billing.Treeview", background=[("selected", "#FBE3E0")],
                  foreground=[("selected", self.DARK)])
        style.layout("Billing.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    # ── History logic ────────────────────────────────────────────────────────

    def _filter_entries(self, entries, query, flt):
        query = (query or "").strip().lower()
        out = []
        for e in entries:
            if flt == "Outstanding" and not _is_outstanding(e):
                continue
            if flt == "Paid" and not (e.get("doc_type") == "invoice" and e.get("status") == "Paid"):
                continue
            if flt == "Receipts" and e.get("doc_type") != "receipt":
                continue
            if query and not any(query in str(e.get(k, "")).lower() for k in
                                 ("client_name", "number", "doc_type", "description",
                                  "client_email", "receipt_number", "from_invoice")):
                continue
            out.append(e)
        return out

    def _refresh_history(self, *_):
        """Reload history from disk and redraw everything that shows it."""
        self._history_all = _load_history()
        total = len(self._history_all)

        # sidebar
        self._store_bar.set(min(total / MAX_HISTORY, 1))
        self._store_lbl.configure(text=f"{total:,} of {MAX_HISTORY:,} records")
        self._store_bar.configure(progress_color="#FCD34D" if total >= WARN_HISTORY else "#4ADE80")
        self._nav_btns["hist"][0].configure(text=f"     History   ({total:,})")
        self._nav_btns["hist"][1].configure(text=f"History ({total:,})")
        self._top_store_lbl.configure(text=f"{total:,} / {MAX_HISTORY:,} records")

        # tiles
        today = date.today()
        month = [e for e in self._history_all
                 if (d := _entry_date(e)) and d.year == today.year and d.month == today.month]
        owed = [e for e in self._history_all if _is_outstanding(e)]
        received = [e for e in month if e.get("doc_type") == "receipt"]
        n_inv = sum(1 for e in month if e.get("doc_type") == "invoice")
        tiles = [
            (f"£{sum(map(_entry_total, owed)):,.2f}", f"{len(owed)} unpaid invoice(s)", self.WARN),
            (f"£{sum(map(_entry_total, received)):,.2f}", f"{len(received)} receipt(s) issued", self.SUCCESS),
            (f"{len(month)}", f"{n_inv} invoice(s), {len(month) - n_inv} receipt(s)", self.DARK),
            (f"{total:,} / {MAX_HISTORY:,}",
             "Nearly full: export and tidy soon" if total >= WARN_HISTORY else "Backed up daily",
             self.WARN if total >= WARN_HISTORY else self.DARK),
        ]
        for (v, n), (value, note, color) in zip(self._tiles, tiles):
            v.configure(text=value, text_color=color)
            n.configure(text=note)

        self._render_recent()
        self._apply_history_filter()

    def _apply_history_filter(self):
        self._history_filtered = self._filter_entries(
            self._history_all, self._hist_search.get(), self._hist_filter.get())
        self._tree.delete(*self._tree.get_children())
        for i, e in enumerate(self._history_filtered):
            status = e.get("status", "")
            tags = ["odd"] if i % 2 else []
            if _is_outstanding(e):
                tags.append("outstanding")
            d = _entry_date(e)
            link = ""
            if e.get("receipt_number"):
                link = f"Receipt {e['receipt_number']}"
            elif e.get("from_invoice"):
                link = f"For {e['from_invoice']}"
            self._tree.insert("", "end", iid=str(i), tags=tags, values=(
                "Invoice" if e.get("doc_type") == "invoice" else "Receipt",
                e.get("number", ""),
                e.get("client_name", ""),
                e.get("description", "").replace("\n", " "),
                d.strftime("%d %b %Y") if d else "",
                f"£{_entry_total(e):,.2f}",
                "Outstanding" if status == "Payment Outstanding" else status,
                link,
            ))
        shown, total = len(self._history_filtered), len(self._history_all)
        self._hist_count_lbl.configure(text=f"Showing {shown:,} of {total:,}")
        self._update_action_buttons()

    def _selected_entry(self):
        sel = self._tree.selection() if hasattr(self, "_tree") else ()
        if not sel:
            return None
        try:
            return self._history_filtered[int(sel[0])]
        except (ValueError, IndexError):
            return None

    def _update_action_buttons(self):
        e = self._selected_entry()
        self._pay_btn.configure(state="normal" if e and e.get("doc_type") == "invoice" else "disabled")
        self._load_btn.configure(state="normal" if e else "disabled")
        has_pdf = bool(e and e.get("pdf_path") and os.path.exists(e["pdf_path"]))
        self._pdf_btn.configure(state="normal" if has_pdf else "disabled")

    def _open_selected_pdf(self):
        e = self._selected_entry()
        if not e:
            return
        path = e.get("pdf_path", "")
        if path and os.path.exists(path):
            _open_file(path)
        else:
            messagebox.showinfo("PDF Not Found",
                                "This record has no saved PDF location, or the file has been moved.\n"
                                "Records created before this update do not store their PDF location.")

    def _new_invoice(self):
        self._clear_form()
        self._doc_type.set("invoice")
        self._show_page("new")

    # ── Export (date range, read-only) ───────────────────────────────────────

    def _export_history(self):
        ExportDialog(self)

    # ── Mark paid → receipt ──────────────────────────────────────────────────

    def _invoice_to_receipt(self):
        """Mark the selected invoice as paid and create its receipt with a new receipt number."""
        inv = self._selected_entry()
        if not inv:
            messagebox.showinfo("Select an Invoice",
                                "Click an invoice in the history list first, then choose Mark paid.")
            return
        if inv.get("doc_type") != "invoice":
            messagebox.showinfo("Not an Invoice",
                                "This record is already a receipt. Select an invoice instead.")
            return
        try:
            exc  = float(inv.get("amount_exc", 0))
            rate = float(inv.get("vat_rate", 20))
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Amount",
                                 "This invoice has an unreadable amount. Load it into the form "
                                 "and generate the receipt manually.")
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

        today_str  = _today_str()
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
        out_path = _pdf_path(out_dir, "receipt", rec_number, data["client_name"])

        try:
            generate_receipt(data, out_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate receipt:\n{e}")
            return

        _save_history_entry({
            **{k: data[k] for k in ("number", "doc_type", "date", "client_name", "client_address",
                                    "client_phone", "client_email", "description", "course_date",
                                    "amount_exc", "vat_rate", "status")},
            "from_invoice":   inv.get("number", ""),
            "pdf_path":       out_path,
            "generated_at":   datetime.today().isoformat(timespec="seconds"),
        })
        _update_history_entry(inv, {"status": "Paid", "receipt_number": rec_number,
                                    "paid_on": today_str})
        self._refresh_doc_number()
        self._refresh_history()
        self._set_status(f"{inv.get('number')} marked Paid. Receipt {rec_number} saved.")
        if messagebox.askyesno("Receipt Created",
                               f"Receipt {rec_number} saved to:\n{out_path}\n\nOpen it now?"):
            _open_file(out_path)

    def _load_from_history(self, event=None):
        entry = self._selected_entry()
        if not entry:
            return
        self._doc_type.set(entry.get("doc_type", "invoice"))
        self._set(self.f_name,    entry.get("client_name", ""))
        self._set(self.f_address, entry.get("client_address", ""))
        self._set(self.f_phone,   entry.get("client_phone", ""))
        self._set(self.f_email,   entry.get("client_email", ""))
        self._set(self.f_desc,    entry.get("description", ""))
        self._set(self.f_cdate,   entry.get("course_date", ""))
        self._set(self.f_exc,     entry.get("amount_exc", ""))
        self._set(self.f_vat,     entry.get("vat_rate", "20"))
        self._set(self.f_date,    _today_str())
        status = entry.get("status", "Payment Outstanding")
        self._status_var.set(status if status in PAYMENT_STATUSES else "Payment Outstanding")
        self._course_var.set(COURSE_PLACEHOLDER)
        self._update_total()
        self._refresh_doc_number()
        self._show_page("new")
        self._set_status(f"Loaded {entry.get('client_name', '')}. Review the details, then Generate.",
                         self.DARK)

    # ── Form logic ───────────────────────────────────────────────────────────

    def _on_doc_type_changed(self, *_):
        t = self._doc_type.get()
        label = "Invoice" if t == "invoice" else "Receipt"
        if self._type_seg.get() != label:
            self._type_seg.set(label)
        self._doc_num_lbl_var.set(f"{label.upper()} NUMBER")
        self._gen_btn.configure(text=f"Generate {label.lower()} PDF")
        self._refresh_doc_number()

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._out_dir.get())
        if d:
            self._out_dir.set(d)
            _save_location(d)

    def _update_total(self, _event=None):
        try:
            exc  = float(self._get(self.f_exc) or 0)
            rate = float(self._get(self.f_vat) or 20)
            vat  = exc * rate / 100
            self._sub_var.set(f"£{exc:,.2f}")
            self._vat_lbl_var.set(f"VAT ({rate:g}%)")
            self._vat_var.set(f"£{vat:,.2f}")
            self._total_var.set(f"£{exc + vat:,.2f}")
        except ValueError:
            for v in (self._sub_var, self._vat_var, self._total_var):
                v.set("—")

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

    def _clear_form(self):
        for w in (self.f_name, self.f_email, self.f_phone, self.f_address,
                  self.f_desc, self.f_cdate, self.f_exc):
            self._set(w, "")
        self._set(self.f_vat, "20")
        self._set(self.f_date, _today_str())
        self._status_var.set("Payment Outstanding")
        self._course_var.set(COURSE_PLACEHOLDER)
        self._update_total()
        self._refresh_doc_number()
        self._set_status("")
        self.f_name.focus_set()

    # ── Course library ───────────────────────────────────────────────────────

    def _refresh_course_combo(self):
        names = [c["name"] for c in _load_courses()] + ["+ Add new course…"]
        self._course_combo.configure(values=names)

    def _on_course_selected(self, val=None):
        val = val or self._course_var.get()
        if val == "+ Add new course…":
            self._course_var.set(COURSE_PLACEHOLDER)
            self._open_course_manager()
            return
        match = next((c for c in _load_courses() if c["name"] == val), None)
        if not match:
            return
        self._set(self.f_desc, match["name"])
        rate = float(match.get("vat_rate", 20))
        exc  = float(match["price_inc"]) / (1 + rate / 100)
        self._set(self.f_exc, f"{exc:.2f}")
        self._set(self.f_vat, f"{rate:g}")
        self._update_total()

    def _open_course_manager(self):
        CourseManager(self)

    # ── Validation & generation ──────────────────────────────────────────────

    def _validate(self):
        required = {
            "Full name":          self.f_name,
            "Address":            self.f_address,
            "Phone":              self.f_phone,
            "Email":              self.f_email,
            "Document date":      self.f_date,
            "Course description": self.f_desc,
            "Course date":        self.f_cdate,
            "Amount exc. VAT":    self.f_exc,
            "VAT rate":           self.f_vat,
        }
        for name, widget in required.items():
            if not self._get(widget):
                messagebox.showerror("Missing Field", f"Please fill in: {name}")
                widget.focus_set()
                return False
        try:
            float(self._get(self.f_exc))
            float(self._get(self.f_vat))
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount and VAT rate must be numbers.")
            return False
        return True

    def _generate(self):
        if not self._validate():
            return
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
        out_dir = self._out_dir.get()
        if not os.path.isdir(out_dir):
            messagebox.showerror("Folder Not Found",
                                 f"The save folder does not exist:\n{out_dir}\n\nChoose another with Browse.")
            return
        out_path = _pdf_path(out_dir, doc_type, auto_number, data["client_name"])

        label = "invoice" if doc_type == "invoice" else "receipt"
        try:
            self._gen_btn.configure(text="Generating…", state="disabled")
            self.update_idletasks()
            if doc_type == "invoice":
                generate_invoice(data, out_path)
            else:
                generate_receipt(data, out_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{e}")
            return
        finally:
            self._gen_btn.configure(text=f"Generate {label} PDF", state="normal")

        _save_location(out_dir)
        _save_history_entry({
            **{k: data[k] for k in ("number", "doc_type", "date", "client_name", "client_address",
                                    "client_phone", "client_email", "description", "course_date",
                                    "amount_exc", "vat_rate", "status")},
            "pdf_path":     out_path,
            "generated_at": datetime.today().isoformat(timespec="seconds"),
        })
        self._refresh_doc_number()
        self._refresh_history()
        self._set_status(f"Saved {auto_number}: {out_path}")

        total = len(self._history_all)
        if total >= WARN_HISTORY:
            messagebox.showwarning(
                "History Nearly Full",
                f"You have {total:,} of {MAX_HISTORY:,} history entries saved.\n"
                "Consider exporting old records soon.")
        if messagebox.askyesno("Done!", f"PDF saved to:\n{out_path}\n\nOpen it now?"):
            _open_file(out_path)


# ─────────────────────────────────────────────────────────────────────────────
#  Dialogs
# ─────────────────────────────────────────────────────────────────────────────

def _modal(win, parent, title, size):
    win.title(title)
    w, h = (int(v) for v in size.split("x"))
    try:
        scale = ctk.ScalingTracker.get_window_scaling(parent)
        px = parent.winfo_rootx() / scale + (parent.winfo_width() / scale - w) / 2
        py = parent.winfo_rooty() / scale + (parent.winfo_height() / scale - h) / 3
        win.geometry(f"{w}x{h}+{max(int(px), 0)}+{max(int(py), 0)}")
    except Exception:
        win.geometry(size)
    win.configure(fg_color=parent.BG)
    win.transient(parent)
    win.resizable(False, False)

    def _grab():
        try:
            win.grab_set()
            win.focus_force()
        except tk.TclError:
            pass
    win.after(120, _grab)
    if sys.platform == "win32":
        ico = resource_path("logo.ico")
        if os.path.exists(ico):
            win.after(260, lambda: win.iconbitmap(ico))


class ExportDialog(ctk.CTkToplevel):
    """Export history to CSV for a chosen date range. Read-only: never changes history."""

    def __init__(self, app: App):
        super().__init__(app)
        self.app = app
        _modal(self, app, "Export history to CSV", "540x590")
        self.grid_columnconfigure(0, weight=1)

        self.mode    = tk.StringVar(value="range")
        self.use_flt = tk.BooleanVar(value=False)

        ctk.CTkLabel(self, text="Export history to CSV", font=app.F_H2, text_color=app.DARK,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=24, pady=(22, 2))
        ctk.CTkLabel(self, text="Choose which records to include. The file opens in Excel.",
                     font=app.F_SM, text_color=app.MUTED, anchor="w").grid(row=1, column=0, sticky="w", padx=24)

        card = ctk.CTkFrame(self, fg_color=app.PANEL, corner_radius=12, border_width=1,
                            border_color=app.BORDER)
        card.grid(row=2, column=0, sticky="ew", padx=24, pady=(16, 0))
        card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkRadioButton(card, text="Date range", variable=self.mode, value="range",
                           font=app.F_B, text_color=app.DARK, fg_color=app.ACCENT,
                           hover_color=app.ACCENT2, command=self._update).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 4))
        ctk.CTkRadioButton(card, text="All dates", variable=self.mode, value="all",
                           font=app.F_B, text_color=app.DARK, fg_color=app.ACCENT,
                           hover_color=app.ACCENT2, command=self._update).grid(
            row=0, column=1, sticky="w", padx=18, pady=(16, 4))

        today = date.today()
        self.e_from = self._date_field(card, "From (DD/MM/YYYY)", 1, 0,
                                       today.replace(day=1).strftime("%d/%m/%Y"))
        self.e_to   = self._date_field(card, "To (DD/MM/YYYY)", 1, 1, today.strftime("%d/%m/%Y"))

        quick = ctk.CTkFrame(card, fg_color="transparent")
        quick.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 16))
        quick.grid_columnconfigure((0, 1), weight=1)
        for i, (label, fn) in enumerate([("This month", self._this_month),
                                         ("Last month", self._last_month),
                                         ("This tax year (from 6 April)", self._this_tax_year),
                                         ("Last tax year", self._last_tax_year)]):
            ctk.CTkButton(quick, text=label, command=fn, height=34, corner_radius=17,
                          font=app.F_SM, fg_color="#F1F2F5", hover_color="#E4E6EA",
                          text_color=app.DARK).grid(row=i // 2, column=i % 2, sticky="ew",
                                                    padx=6, pady=4)

        ctk.CTkCheckBox(self, text="Only records matching the current History search and filter",
                        variable=self.use_flt, font=app.F_SM, text_color=app.DARK,
                        fg_color=app.ACCENT, hover_color=app.ACCENT2, command=self._update).grid(
            row=3, column=0, sticky="w", padx=26, pady=(16, 0))

        self.count_lbl = ctk.CTkLabel(self, text="", font=app.F_B, text_color=app.DARK, anchor="w")
        self.count_lbl.grid(row=4, column=0, sticky="w", padx=26, pady=(16, 0))
        ctk.CTkLabel(self, text="Exporting only copies records into a file. "
                                "Nothing is removed from your history.",
                     font=app.F_SM, text_color=app.MUTED, anchor="w", wraplength=460,
                     justify="left").grid(row=5, column=0, sticky="w", padx=26, pady=(4, 0))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=6, column=0, sticky="e", padx=24, pady=(22, 22))
        app._secondary(btns, "Cancel", self.destroy).grid(row=0, column=0, padx=(0, 10))
        self.go_btn = app._primary(btns, "Export CSV", self._export)
        self.go_btn.grid(row=0, column=1)

        for e in (self.e_from, self.e_to):
            e.bind("<KeyRelease>", lambda *_: self._update())
        self._update()

    def _date_field(self, parent, label, row, col, value):
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=row, column=col, sticky="ew", padx=18, pady=(8, 8))
        cell.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(cell, text=label, font=self.app.F_SM, text_color=self.app.MUTED,
                     anchor="w", height=18).grid(row=0, column=0, sticky="w", pady=(0, 4))
        e = ctk.CTkEntry(cell, height=38, font=self.app.F, corner_radius=8, border_width=1,
                         border_color=self.app.FIELD_BD, fg_color=self.app.INP_BG,
                         text_color=self.app.INP_FG)
        e.insert(0, value)
        e.grid(row=1, column=0, sticky="ew")
        return e

    def _set_range(self, start, end):
        self.mode.set("range")
        for e, d in ((self.e_from, start), (self.e_to, end)):
            e.delete(0, "end")
            e.insert(0, d.strftime("%d/%m/%Y"))
        self._update()

    def _this_month(self):
        t = date.today()
        self._set_range(t.replace(day=1), t)

    def _last_month(self):
        first_this = date.today().replace(day=1)
        last_prev  = first_this - timedelta(days=1)
        self._set_range(last_prev.replace(day=1), last_prev)

    @staticmethod
    def _tax_year_start(d):
        start = date(d.year, 4, 6)
        return start if d >= start else date(d.year - 1, 4, 6)

    def _this_tax_year(self):
        t = date.today()
        self._set_range(self._tax_year_start(t), t)

    def _last_tax_year(self):
        start_this = self._tax_year_start(date.today())
        self._set_range(date(start_this.year - 1, 4, 6), date(start_this.year, 4, 5))

    def _selection(self):
        """Return (entries, error_message, start, end) without changing anything."""
        entries = list(self.app._history_all)
        if self.use_flt.get():
            entries = self.app._filter_entries(entries, self.app._hist_search.get(),
                                               self.app._hist_filter.get())
        start = end = None
        if self.mode.get() == "range":
            start = _parse_user_date(self.e_from.get())
            end   = _parse_user_date(self.e_to.get())
            if not start or not end:
                return [], "Enter both dates as DD/MM/YYYY.", None, None
            if start > end:
                return [], "The From date is after the To date.", None, None
            entries = [e for e in entries if (d := _entry_date(e)) and start <= d <= end]
        entries.sort(key=lambda e: (_entry_date(e) or date.min, e.get("generated_at", "")))
        return entries, "", start, end

    def _update(self):
        state = "normal" if self.mode.get() == "range" else "disabled"
        for e in (self.e_from, self.e_to):
            e.configure(state=state)
        entries, err, *_ = self._selection()
        if err:
            self.count_lbl.configure(text=err, text_color=self.app.ACCENT)
            self.go_btn.configure(state="disabled")
        else:
            n = len(entries)
            self.count_lbl.configure(text=f"{n:,} record(s) will be exported",
                                     text_color=self.app.DARK)
            self.go_btn.configure(state="normal" if n else "disabled")

    def _export(self):
        entries, err, start, end = self._selection()
        if err or not entries:
            return
        if start:
            default_name = f"billing_history_{start:%Y-%m-%d}_to_{end:%Y-%m-%d}.csv"
        else:
            default_name = f"billing_history_all_{date.today():%Y-%m-%d}.csv"
        out_dir = self.app._out_dir.get()
        out_path = filedialog.asksaveasfilename(
            parent=self, title="Save CSV export",
            initialdir=out_dir if os.path.isdir(out_dir) else _get_saved_location(),
            initialfile=default_name, defaultextension=".csv",
            filetypes=[("CSV (opens in Excel)", "*.csv"), ("All files", "*.*")])
        if not out_path:
            return
        try:
            export_history_csv(entries, out_path)
        except PermissionError:
            messagebox.showerror("Export Failed", "Could not write the file. If it is open in "
                                 "Excel, close it and try again.", parent=self)
            return
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export history:\n{e}", parent=self)
            return
        self.app._set_status(f"Exported {len(entries):,} record(s) to {out_path}")
        self.destroy()
        if messagebox.askyesno("Export Complete",
                               f"Exported {len(entries):,} record(s) to:\n{out_path}\n\n"
                               "Your history has not been changed.\n\nOpen the file now?"):
            _open_file(out_path)


class CourseManager(ctk.CTkToplevel):
    """Add, edit and delete courses in the course library."""

    def __init__(self, app: App):
        super().__init__(app)
        self.app = app
        self.editing = None
        _modal(self, app, "Course library", "760x560")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Course library", font=app.F_H2, text_color=app.DARK,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Double-click a course to edit it. Prices include VAT.",
                     font=app.F_SM, text_color=app.MUTED, anchor="w").grid(row=1, column=0, sticky="w", padx=24)

        box = ctk.CTkFrame(self, fg_color=app.PANEL, corner_radius=12, border_width=1,
                           border_color=app.BORDER)
        box.grid(row=2, column=0, sticky="nsew", padx=24, pady=(12, 0))
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(box, columns=("name", "price", "vat"), show="headings",
                                 style="Billing.Treeview", selectmode="browse")
        for c, h, w, a in (("name", "Course name", 470, "w"), ("price", "Price inc. VAT", 130, "e"),
                           ("vat", "VAT %", 70, "e")):
            self.tree.heading(c, text=h, anchor=a)
            self.tree.column(c, width=w, anchor=a, stretch=c == "name")
        self.tree.tag_configure("odd", background="#FAFAFB")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=2)
        sb = ctk.CTkScrollbar(box, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 4))
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-Button-1>", self._edit)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=3, column=0, sticky="ew", padx=16, pady=(12, 0))
        form.grid_columnconfigure(0, weight=1)
        self.e_name  = app._field(form, "Course name", 0, 0)
        self.e_price = app._field(form, "Price inc. VAT (£)", 0, 1)
        self.e_vat   = app._field(form, "VAT %", 0, 2)
        form.grid_columnconfigure(1, minsize=150)
        form.grid_columnconfigure(2, minsize=90)
        self.e_vat.insert(0, "20")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=4, column=0, sticky="ew", padx=24, pady=(10, 20))
        btns.grid_columnconfigure(2, weight=1)
        self.save_btn = app._primary(btns, "Add course", self._save)
        self.save_btn.grid(row=0, column=0)
        ctk.CTkButton(btns, text="Delete selected", command=self._delete, height=40,
                      corner_radius=10, font=app.F, fg_color="#FDECEA", hover_color="#F9D9D5",
                      text_color=app.ACCENT).grid(row=0, column=1, padx=10)
        app._secondary(btns, "Close", self.destroy).grid(row=0, column=3)
        self._reload()

    def _reload(self):
        self.tree.delete(*self.tree.get_children())
        self.courses = _load_courses()
        for i, c in enumerate(self.courses):
            self.tree.insert("", "end", iid=str(i), tags=["odd"] if i % 2 else [],
                             values=(c["name"], f"£{float(c['price_inc']):.2f}",
                                     f"{float(c.get('vat_rate', 20)):g}"))

    def _reset_form(self):
        self.editing = None
        for e in (self.e_name, self.e_price, self.e_vat):
            e.delete(0, "end")
        self.e_vat.insert(0, "20")
        self.save_btn.configure(text="Add course")

    def _edit(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.editing = int(sel[0])
        c = self.courses[self.editing]
        for e, v in ((self.e_name, c["name"]), (self.e_price, f"{float(c['price_inc']):.2f}"),
                     (self.e_vat, f"{float(c.get('vat_rate', 20)):g}")):
            e.delete(0, "end")
            e.insert(0, v)
        self.save_btn.configure(text="Save changes")

    def _save(self):
        name, price, vat = (e.get().strip() for e in (self.e_name, self.e_price, self.e_vat))
        if not name or not price:
            messagebox.showerror("Missing", "Course name and price are required.", parent=self)
            return
        try:
            price_f, vat_f = float(price), float(vat or 20)
        except ValueError:
            messagebox.showerror("Invalid", "Price and VAT must be numbers.", parent=self)
            return
        courses = _load_courses()
        entry = {"name": name, "price_inc": price_f, "vat_rate": vat_f}
        if self.editing is not None and self.editing < len(courses):
            courses[self.editing] = entry
        else:
            courses.append(entry)
        _save_courses(courses)
        self._reset_form()
        self._reload()
        self.app._refresh_course_combo()

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        c = self.courses[int(sel[0])]
        if not messagebox.askyesno("Delete Course", f"Remove this course from the library?\n\n{c['name']}",
                                   parent=self):
            return
        courses = [x for i, x in enumerate(_load_courses()) if i != int(sel[0])]
        _save_courses(courses)
        self._reset_form()
        self._reload()
        self.app._refresh_course_combo()


if __name__ == "__main__":
    _backup_settings_daily()
    app = App()
    app.mainloop()
