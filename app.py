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

# Settings file — stores counters, last save location, and history
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), "fat_generator_settings.json")
MAX_HISTORY = 50


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
    import json
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def _parse_date_from_field(date_str: str):
    formats = [
        "%d %B %Y", "%#d %B %Y", "%-d %B %Y",
        "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
    ]
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
    s = _load_settings()
    history = s.get("history", [])
    history.insert(0, entry)
    s["history"] = history[:MAX_HISTORY]
    _save_settings(s)


def _load_history() -> list:
    return _load_settings().get("history", [])

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
        tk.Label(hist_hdr, text="🕐  Document History",
                 font=self.FONT_B, bg=self.DARK, fg="white").pack(side="left", padx=12, pady=8)
        tk.Label(hist_hdr,
                 text="Click a row to reload its details into the form (date will be today's)",
                 font=self.FONT_SH, bg=self.DARK, fg="#9CA3AF").pack(side="left", padx=(0,8))

        # Search box
        search_frame = tk.Frame(hist_outer, bg=self.BG)
        search_frame.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(search_frame, text="Search:", font=self.FONT_SH,
                 bg=self.BG, fg=self.MUTED).pack(side="left")
        self._hist_search = tk.Entry(search_frame, font=self.FONT_SH,
                                     bg=self.INP_BG, fg=self.INP_FG,
                                     relief="flat", bd=0,
                                     highlightthickness=1, highlightbackground=self.BORDER)
        self._hist_search.pack(side="left", fill="x", expand=True, ipady=5, ipadx=6, padx=(6,0))
        self._hist_search.bind("<KeyRelease>", lambda *_: self._refresh_history())

        # Listbox with scrollbar
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

        # Store raw history for filtering
        self._history_data = []
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
        # Refresh preview as user edits date
        self.f_date.bind("<KeyRelease>", self._refresh_doc_number)
        self.f_date.bind("<FocusOut>",   self._refresh_doc_number)

        self._divider(parent)

        # ── Course details ───────────────────────────────────────────────────
        self._section(parent, "🏫  Course Details")
        course_grid = tk.Frame(parent, bg=self.BG)
        course_grid.pack(fill="x", padx=18)

        self.f_desc  = self._field(course_grid, "Course Description *", row=0, col=0,
                                    multiline=True, colspan=2)
        self.f_cdate = self._field(course_grid, "Course Date *",         row=1, col=0)

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
        """Reload listbox from persisted history, filtered by search box."""
        query = self._hist_search.get().strip().lower() if hasattr(self, "_hist_search") else ""
        self._history_data = _load_history()

        filtered = [
            e for e in self._history_data
            if query in e.get("client_name", "").lower()
            or query in e.get("number", "").lower()
            or query in e.get("doc_type", "").lower()
            or query in e.get("description", "").lower()
        ] if query else self._history_data

        self._hist_lb.delete(0, "end")
        for e in filtered:
            dt   = e.get("doc_type", "?")[0].upper()          # I / R
            num  = e.get("number", "—")
            name = e.get("client_name", "—")
            gen  = e.get("generated_at", "")[:10]             # date only
            exc  = e.get("amount_exc", "")
            total_str = ""
            try:
                exc_f  = float(exc)
                rate_f = float(e.get("vat_rate", 20))
                total_str = f"  £{exc_f*(1+rate_f/100):.2f}"
            except Exception:
                pass
            label = f"[{dt}] {num:<18} {name:<28} {gen}{total_str}"
            self._hist_lb.insert("end", label)
        # store filtered reference so we can look up by index
        self._history_filtered = filtered

    def _load_from_history(self, event=None):
        """Populate all form fields from the selected history entry."""
        sel = self._hist_lb.curselection()
        if not sel:
            return
        entry = self._history_filtered[sel[0]]

        # Switch doc type
        self._doc_type.set(entry.get("doc_type", "invoice"))

        # Helper to set a widget value
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

        # Set date to TODAY (not the original date)
        _day_fmt = "%#d" if sys.platform == "win32" else "%-d"
        today_str = datetime.today().strftime(f"{_day_fmt} %B %Y")
        _set(self.f_date, today_str)

        # Restore payment status
        status = entry.get("status", "Payment Outstanding")
        self._status_var.set(status)

        # Refresh live total and doc number
        self._update_total()
        self._refresh_doc_number()

        # Give user feedback
        self._status_lbl.configure(
            text=f"✏️  Loaded: {entry.get('client_name','')} — edit if needed, then Generate",
            fg=self.DARK
        )

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
        doc_type    = self._doc_type.get()
        date_entered = self._get(self.f_date)
        auto_number = _get_next_doc_number(doc_type, date_entered)
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

        name_safe = re.sub(r'[^\w\-]', '', data["client_name"].replace(" ", "_"))
        doc_label = "invoice" if doc_type == "invoice" else "receipt"
        filename  = f"{doc_label}_{name_safe}.pdf"
        out_path  = os.path.join(self._out_dir.get(), filename)

        try:
            self._gen_btn.configure(text="⏳  Generating…", state="disabled")
            self.update()
            if doc_type == "invoice":
                generate_invoice(data, out_path)
            else:
                generate_receipt(data, out_path)

            self._gen_btn.configure(text="⬇  Generate PDF", state="normal")
            self._status_lbl.configure(text=f"✅  Saved: {out_path}", fg=self.SUCCESS)

            # Persist location, save to history, refresh preview
            _save_location(self._out_dir.get())
            _save_history_entry({
                "number":      auto_number,
                "doc_type":    doc_type,
                "client_name": data["client_name"],
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
    app = App()
    app.mainloop()
