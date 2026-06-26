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


def _truncate_to_width(c, text: str, max_w: float, font: str = "Helvetica", size: int = 9) -> str:
    """Return text truncated with an ellipsis so it fits inside max_w."""
    if not text:
        return ""
    if c.stringWidth(text, font, size) <= max_w:
        return text
    ell = "…"
    # binary search for fit
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if c.stringWidth(text[:mid] + ell, font, size) <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return (text[:lo] + ell) if lo > 0 else ell


def _draw_truncated(c, x: float, y: float, text: str, max_w: float, font: str = "Helvetica", size: int = 9):
    c.drawString(x, y, _truncate_to_width(c, text, max_w, font, size))


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
    # Align both blocks: same header height, same total body height.
    cust_y_top = by - 20 * mm
    header_h = 6 * mm
    cust = invoice.get("customer", {})
    cust_rows = [
        ("Customer TRN:", cust.get("customer_trn", "")),
        ("To M/s:", cust.get("contact_person", "")),
        ("Company Name:", cust.get("company_name", "")),
        ("Address:", cust.get("address", "")),
        ("Ph. No.:", cust.get("phone", "")),
        ("E-mail:", cust.get("email", "")),
    ]
    meta_rows = [
        ("INVOICE NO.:", invoice.get("invoice_no", "")),
        ("DATE:", invoice.get("date", "")),
        ("D.O./NO.:", invoice.get("do_no", "")),
        ("L.P.O. NO.:", invoice.get("lpo_no", "")),
    ]
    # Body heights are equal across both blocks
    cust_body_h = 36 * mm
    cust_row_h = cust_body_h / len(cust_rows)        # 6 mm each
    meta_row_h = cust_body_h / len(meta_rows)        # 9 mm each
    body_top = cust_y_top - header_h
    body_bot = body_top - cust_body_h

    # --- Left: Customer Details ---
    cust_box_w = 110 * mm
    # Header bar
    c.setFillColor(ORANGE)
    c.rect(L, body_top, cust_box_w, header_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(L + cust_box_w / 2, body_top + 1.8 * mm, "Customer Details:")
    # Body outer box
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.7)
    c.rect(L, body_bot, cust_box_w, cust_body_h, stroke=1, fill=0)
    label_w = 32 * mm
    for i, (k, v) in enumerate(cust_rows):
        y = body_top - (i + 1) * cust_row_h
        # label cell shaded
        c.setFillColor(colors.HexColor("#F5F5F5"))
        c.rect(L, y, label_w, cust_row_h, stroke=0, fill=1)
        # internal lines
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.4)
        c.line(L + label_w, y, L + label_w, y + cust_row_h)
        if i < len(cust_rows) - 1:
            c.line(L, y, L + cust_box_w, y)
        # label + value
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(L + 1.5 * mm, y + 1.8 * mm, k)
        c.setFont("Helvetica", 9)
        _draw_truncated(c, L + label_w + 2 * mm, y + 1.8 * mm, str(v), cust_box_w - label_w - 4 * mm, "Helvetica", 9)

    # --- Right: Invoice meta (same total height as Customer block) ---
    meta_x = L + 120 * mm
    meta_w = R - meta_x
    # No top header bar — the orange labels themselves act as headers
    # Outer box for the whole meta block, height = header_h + cust_body_h to align bottoms
    meta_total_h = header_h + cust_body_h
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.7)
    c.rect(meta_x, body_bot, meta_w, meta_total_h, stroke=1, fill=0)
    # Distribute the meta rows over the full meta_total_h
    full_row_h = meta_total_h / len(meta_rows)
    for i, (k, v) in enumerate(meta_rows):
        y = cust_y_top - (i + 1) * full_row_h
        # left orange label cell
        c.setFillColor(ORANGE)
        c.rect(meta_x, y, meta_w * 0.5, full_row_h, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(meta_x + 2 * mm, y + full_row_h / 2 - 1.2 * mm, k)
        # right value cell border
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.4)
        c.line(meta_x + meta_w * 0.5, y, meta_x + meta_w * 0.5, y + full_row_h)
        if i < len(meta_rows) - 1:
            c.line(meta_x, y, meta_x + meta_w, y)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        _draw_truncated(c, meta_x + meta_w * 0.5 + 2 * mm, y + full_row_h / 2 - 1.2 * mm,
                        str(v), meta_w * 0.5 - 4 * mm, "Helvetica", 9)

    # ---------- ITEMS TABLE ----------
    table_top = body_bot - 6 * mm
    headers = ["S.NO.", "DESCRIPTION", "QTY", "UNIT", "Unit Price", "Total Exct. VAT", "Unit VAT 5%", "Total Incl. VAT"]
    col_widths = [12 * mm, 60 * mm, 12 * mm, 14 * mm, 20 * mm, 26 * mm, 20 * mm, 26 * mm]
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
            qty = float(it.get("qty", 0) or 0)
            price = float(it.get("unit_price", 0) or 0)
            vat_pct = float(it.get("vat_percent", 5) or 0)
            vat_amt = qty * price * (vat_pct / 100)
            cells = [
                str(r + 1),
                str(it.get("description", "")),
                _fmt(qty) if qty else "",
                str(it.get("unit", "")),
                _fmt(price) if price else "",
                _fmt(it.get("total_excl", qty * price)),
                _fmt(vat_amt),
                _fmt(it.get("total_incl", qty * price + vat_amt)),
            ]
        else:
            # Empty row: blank cells (no 0.00 fillers)
            cells = ["", "", "", "", "", "", "", ""]
        cx = L
        for i, val in enumerate(cells):
            align = "left" if i == 1 else "center" if i in (0, 2, 3) else "right"
            pad = 1.5 * mm
            avail_w = col_widths[i] - 2 * pad
            # Truncate any cell text that would overflow its cell width
            shown = _truncate_to_width(c, str(val), avail_w, "Helvetica", 9)
            tx = cx + pad if align == "left" else cx + col_widths[i] - pad if align == "right" else cx + col_widths[i] / 2
            if align == "center":
                c.drawCentredString(tx, y + 1.8 * mm, shown)
            elif align == "right":
                c.drawRightString(tx, y + 1.8 * mm, shown)
            else:
                c.drawString(tx, y + 1.8 * mm, shown)
            cx += col_widths[i]

    # ---------- TOTALS + WORDS + BANK ----------
    totals_top = y - 4 * mm
    # Net total in Words label
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(colors.black)
    c.drawString(L, totals_top, "Net Total in Words:")
    # Word-wrap the amount-in-words to fit available width (left of totals box)
    words_max_w = 95 * mm  # totals box starts at L + 100mm
    words_text = invoice.get("amount_words", "ZERO DIRHAMS ONLY")
    c.setFont("Helvetica-Bold", 9.5)
    parts = words_text.split(" ")
    lines, cur = [], ""
    for w in parts:
        trial = (cur + " " + w).strip()
        if c.stringWidth(trial, "Helvetica-Bold", 9.5) <= words_max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    for li, line in enumerate(lines[:2]):  # max 2 lines to avoid pushing bank details
        c.drawString(L, totals_top - 5 * mm - li * 4.5 * mm, line)

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
