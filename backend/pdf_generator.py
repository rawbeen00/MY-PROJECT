"""PDF generator that closely matches the Ansary Furniture tax invoice template."""
import os
from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

ORANGE = colors.HexColor("#F58220")
LIGHT_GRAY = colors.HexColor("#E5E5E5")
DARK = colors.HexColor("#1F2937")

ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "uploads"


def _asset_path(url: str):
    """Resolve a /api/uploads/<name> URL to an absolute file path on disk."""
    if not url:
        return None
    name = url.split("/uploads/")[-1] if "/uploads/" in url else url.lstrip("/")
    p = UPLOAD_DIR / name
    return str(p) if p.exists() else None


def _fmt(n: float) -> str:
    try:
        return f"{float(n):,.2f}"
    except Exception:
        return "0.00"


def _draw_logo(c: canvas.Canvas, x: float, y: float, w: float = 40 * mm) -> None:
    """Draw an SVG-like Ansary Furniture roof logo using primitives."""
    # roof triangle
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    # Outer roof
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + w / 2, y + w * 0.45)
    p.lineTo(x + w, y)
    p.lineTo(x + w * 0.92, y)
    p.lineTo(x + w / 2, y + w * 0.36)
    p.lineTo(x + w * 0.08, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # Orange window block under the roof
    c.setFillColor(ORANGE)
    bw = w * 0.30
    bx = x + (w - bw) / 2
    by = y - w * 0.05
    c.rect(bx, by, bw, w * 0.22, stroke=0, fill=1)
    # window mullions (white cross)
    c.setStrokeColor(colors.white)
    c.setLineWidth(2)
    c.line(bx + bw / 2, by, bx + bw / 2, by + w * 0.22)
    c.line(bx, by + w * 0.11, bx + bw, by + w * 0.11)
    # Title text
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + w / 2, y - w * 0.13, "ANSARY FURNITURE")
    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + w / 2, y - w * 0.20, "LET'S DECORATE YOUR HOME")


def build_invoice_pdf(invoice: dict, settings: dict) -> bytes:
    buf = BytesIO()
    width, height = A4
    c = canvas.Canvas(buf, pagesize=A4)

    L = 12 * mm
    R = width - 12 * mm
    top = height - 12 * mm

    # ---------- HEADER ----------
    logo_file = _asset_path(settings.get("logo_url", ""))
    if logo_file:
        try:
            img = ImageReader(logo_file)
            iw, ih = img.getSize()
            target_w = 40 * mm
            target_h = target_w * (ih / iw)
            if target_h > 26 * mm:
                target_h = 26 * mm
                target_w = target_h * (iw / ih)
            c.drawImage(img, L, top - target_h, width=target_w, height=target_h,
                        mask='auto', preserveAspectRatio=True)
        except Exception:
            _draw_logo(c, L, top - 12 * mm, w=40 * mm)
    else:
        _draw_logo(c, L, top - 12 * mm, w=40 * mm)

    # Center "TAX INVOICE" badge
    badge_w = 60 * mm
    badge_h = 11 * mm
    bx = (width - badge_w) / 2
    by = top - 12 * mm
    c.setFillColor(ORANGE)
    c.rect(bx, by, badge_w, badge_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(bx + badge_w / 2, by + 3.5 * mm, "TAX INVOICE")

    # TRN below the badge
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(bx + badge_w / 2, by - 5 * mm, f"TRN: {settings.get('trn','')}")
    # Address line
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(width / 2, by - 10 * mm, f"Address: {settings.get('address','')}")
    c.drawCentredString(width / 2, by - 13.5 * mm, f"E-mail: {settings.get('email','')}")

    # Right side websites
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    rx = R
    ry = top - 10 * mm
    c.drawRightString(rx, ry, f"{settings.get('website','')} - {settings.get('phone','')}")
    for i, ws in enumerate(settings.get("extra_websites", [])):
        c.drawRightString(rx, ry - (i + 1) * 4.5 * mm, ws)

    # ---------- CUSTOMER + INVOICE DETAILS BLOCK ----------
    cust_y_top = by - 20 * mm
    # Customer Details header bar
    c.setFillColor(ORANGE)
    c.rect(L, cust_y_top - 6 * mm, 110 * mm, 6 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(L + 55 * mm, cust_y_top - 4.3 * mm, "Customer Details:")

    cust = invoice.get("customer", {})
    rows = [
        ("Customer TRN:", cust.get("customer_trn", "")),
        ("To M/s:", cust.get("contact_person", "")),
        ("Company Name:", cust.get("company_name", "")),
        ("Address:", cust.get("address", "")),
        ("Ph. No.:", cust.get("phone", "")),
        ("E-mail:", cust.get("email", "")),
    ]
    row_h = 6 * mm
    box_y = cust_y_top - 6 * mm - len(rows) * row_h
    # Outer box for customer fields
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.7)
    c.rect(L, box_y, 110 * mm, len(rows) * row_h, stroke=1, fill=0)
    label_w = 32 * mm
    for i, (k, v) in enumerate(rows):
        y = cust_y_top - 6 * mm - (i + 1) * row_h
        # alternating shade
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#F5F5F5"))
            c.rect(L, y, label_w, row_h, stroke=0, fill=1)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.4)
        c.line(L + label_w, y, L + label_w, y + row_h)
        c.line(L, y, L + 110 * mm, y)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(L + 1.5 * mm, y + 1.8 * mm, k)
        c.setFont("Helvetica", 9)
        c.drawString(L + label_w + 2 * mm, y + 1.8 * mm, str(v))

    # Right side: Invoice meta
    meta_x = L + 120 * mm
    meta_w = R - meta_x
    meta_rows = [
        ("INVOICE NO.:", invoice.get("invoice_no", "")),
        ("DATE:", invoice.get("date", "")),
        ("D.O./NO.:", invoice.get("do_no", "")),
        ("L.P.O. NO.:", invoice.get("lpo_no", "")),
    ]
    mh = 7 * mm
    for i, (k, v) in enumerate(meta_rows):
        y = cust_y_top - (i + 1) * mh
        c.setFillColor(ORANGE)
        c.rect(meta_x, y, meta_w * 0.5, mh, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(meta_x + 2 * mm, y + 2.2 * mm, k)
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(meta_x + meta_w * 0.5, y, meta_w * 0.5, mh, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(meta_x + meta_w * 0.5 + 2 * mm, y + 2.2 * mm, str(v))

    # ---------- ITEMS TABLE ----------
    table_top = box_y - 6 * mm
    headers = ["S.NO.", "DESCRIPTION", "QTY", "UNIT", "Unit Price", "Unit VAT 5%", "Total Exct. VAT", "Total Incl. VAT"]
    col_widths = [12 * mm, 60 * mm, 12 * mm, 14 * mm, 20 * mm, 20 * mm, 26 * mm, 26 * mm]
    table_width = sum(col_widths)

    # Headers
    c.setFillColor(ORANGE)
    c.rect(L, table_top - 7 * mm, table_width, 7 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    x = L
    for i, h in enumerate(headers):
        c.drawCentredString(x + col_widths[i] / 2, table_top - 4.8 * mm, h)
        x += col_widths[i]

    # Rows — pad to at least 12 rows for visual consistency
    items = invoice.get("items", [])
    min_rows = 12
    total_rows = max(len(items), min_rows)
    row_h = 6 * mm
    c.setFont("Helvetica", 9)
    y = table_top - 7 * mm
    for r in range(total_rows):
        y -= row_h
        if r % 2 == 0:
            c.setFillColor(colors.HexColor("#FAFAFA"))
            c.rect(L, y, table_width, row_h, stroke=0, fill=1)
        # cell borders
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.4)
        c.rect(L, y, table_width, row_h, stroke=1, fill=0)
        cx = L
        for w in col_widths[:-1]:
            cx += w
            c.line(cx, y, cx, y + row_h)
        c.setFillColor(colors.black)
        if r < len(items):
            it = items[r]
            cells = [
                str(r + 1),
                str(it.get("description", "")),
                _fmt(it.get("qty", 0)) if it.get("qty") else "",
                str(it.get("unit", "")),
                _fmt(it.get("unit_price", 0)) if it.get("unit_price") else "",
                _fmt((it.get("qty", 0) * it.get("unit_price", 0)) * (it.get("vat_percent", 5) / 100)),
                _fmt(it.get("total_excl", 0)),
                _fmt(it.get("total_incl", 0)),
            ]
        else:
            cells = ["", "", "", "", "", "0.00", "0.00", "0.00"]
        cx = L
        for i, val in enumerate(cells):
            align = "left" if i == 1 else "center" if i in (0, 2, 3) else "right"
            tx = cx + 1.5 * mm if align == "left" else cx + col_widths[i] - 1.5 * mm if align == "right" else cx + col_widths[i] / 2
            if align == "center":
                c.drawCentredString(tx, y + 1.8 * mm, val)
            elif align == "right":
                c.drawRightString(tx, y + 1.8 * mm, val)
            else:
                c.drawString(tx, y + 1.8 * mm, val)
            cx += col_widths[i]

    # ---------- TOTALS + WORDS + BANK ----------
    totals_top = y - 4 * mm
    # Net total in Words label
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(colors.black)
    c.drawString(L, totals_top, "Net Total in Words:")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(L, totals_top - 5 * mm, invoice.get("amount_words", "ZERO DIRHAMS ONLY"))

    # Totals box (right)
    tx = L + 100 * mm
    tw = R - tx
    rows_t = [
        ("Gross Total (AED)", _fmt(invoice.get("gross_total", 0)), False),
        ("Discount", _fmt(invoice.get("discount", 0)), False),
        ("VAT 5% Included (AED)", _fmt(invoice.get("vat_total", 0)), False),
        ("NET TOTAL (AED)", _fmt(invoice.get("net_total", 0)), True),
    ]
    th = 6.5 * mm
    for i, (k, v, hl) in enumerate(rows_t):
        ty = totals_top - i * th - 2 * mm
        if hl:
            c.setFillColor(ORANGE)
        else:
            c.setFillColor(colors.HexColor("#E5E7EB"))
        c.rect(tx, ty - th, tw * 0.6, th, stroke=1, fill=1)
        c.setFillColor(colors.white if hl else colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(tx + 2 * mm, ty - th + 2.2 * mm, k)
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.rect(tx + tw * 0.6, ty - th, tw * 0.4, th, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(tx + tw - 2 * mm, ty - th + 2.2 * mm, v)

    # ---------- BANK DETAILS ----------
    bank_top = totals_top - 14 * mm
    bank_rows = [
        ("Bank Name:", settings.get("bank_name", "")),
        ("Account Title:", settings.get("account_title", "")),
        ("Account Number:", settings.get("account_number", "")),
        ("IBAN:", settings.get("iban", "")),
        ("Currency:", settings.get("currency", "AED")),
        ("Branch:", settings.get("branch", "")),
        ("Swift Code:", settings.get("swift_code", "")),
    ]
    c.setFillColor(colors.black)
    for i, (k, v) in enumerate(bank_rows):
        by_ = bank_top - i * 4.5 * mm
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(L, by_, k)
        c.setFont("Helvetica", 8.5)
        c.drawString(L + 30 * mm, by_, str(v))

    # Receiver's Sign + Authorized Signature
    sign_y = bank_top - 38 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(L, sign_y, "RECEIVER'S SIGN: ____________________________________")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(L, sign_y - 10 * mm, "T&C Applied:")
    if invoice.get("terms"):
        c.setFont("Helvetica", 8)
        c.drawString(L + 22 * mm, sign_y - 10 * mm, invoice.get("terms", "")[:90])

    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.grey)
    c.drawRightString(R, sign_y - 6 * mm, "Authorized Signature & Stamp")
    c.line(R - 60 * mm, sign_y - 2 * mm, R, sign_y - 2 * mm)

    # Place uploaded signature and stamp above the signature line if present
    sig_file = _asset_path(settings.get("signature_url", ""))
    stamp_file = _asset_path(settings.get("stamp_url", ""))
    try:
        if stamp_file:
            si = ImageReader(stamp_file)
            sw, sh = si.getSize()
            target_h = 22 * mm
            target_w = target_h * (sw / sh)
            c.drawImage(si, R - 58 * mm, sign_y - 2 * mm, width=target_w, height=target_h,
                        mask='auto', preserveAspectRatio=True)
        if sig_file:
            sg = ImageReader(sig_file)
            gw, gh = sg.getSize()
            target_h = 14 * mm
            target_w = target_h * (gw / gh)
            c.drawImage(sg, R - 30 * mm, sign_y - 1 * mm, width=target_w, height=target_h,
                        mask='auto', preserveAspectRatio=True)
    except Exception:
        pass


    # Footer page number
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawRightString(R, 8 * mm, "Page 1 of 1")

    c.showPage()
    c.save()
    return buf.getvalue()
