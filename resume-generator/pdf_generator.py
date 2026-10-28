"""Builds the PDF resume with ReportLab.

Every template is just an entry in THEMES, so adding a new look takes a few
lines. The options are:

  accent   main colour (hex)
  font     "Helvetica" (sans-serif) or "Times-Roman" (serif)
  header   "left", "center" or "band" (name on a coloured banner)
  heading  "rule" (line under title), "bar" (coloured bar beside it)
           or "center" (centered title with a short line)
"""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

THEMES = {
    "classic": {"label": "Classic", "accent": "#1f4e79", "font": "Helvetica",
                "header": "left", "heading": "rule"},
    "modern": {"label": "Modern", "accent": "#0f766e", "font": "Helvetica",
               "header": "left", "heading": "bar"},
    "minimal": {"label": "Minimal", "accent": "#222222", "font": "Helvetica",
                "header": "left", "heading": "rule"},
    "executive": {"label": "Executive", "accent": "#1b2a49", "font": "Times-Roman",
                  "header": "center", "heading": "rule"},
    "elegant": {"label": "Elegant", "accent": "#7f1d1d", "font": "Times-Roman",
                "header": "center", "heading": "center"},
    "bold": {"label": "Bold", "accent": "#4338ca", "font": "Helvetica",
             "header": "band", "heading": "rule"},
}

BOLD_FONT = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold"}

PAGE_MARGIN = 18 * mm
# ReportLab frames have 6pt padding on each side; stay inside it.
FRAME_WIDTH = A4[0] - 2 * PAGE_MARGIN - 12


def _safe(text):
    """Escape user text so characters like & or < cannot break the PDF markup."""
    return escape(text or "")


def _link(url, color="#2563eb"):
    """Make a clickable link, but only for http(s) URLs."""
    if url.lower().startswith(("http://", "https://")):
        href = escape(url, {'"': "&quot;"})
        return f'<link href="{href}" color="{color}">{escape(url)}</link>'
    return escape(url)


def _styles(theme):
    accent = colors.HexColor(theme["accent"])
    font = theme["font"]
    bold = BOLD_FONT[font]
    on_band = theme["header"] == "band"
    header_align = TA_CENTER if theme["header"] == "center" else TA_LEFT
    base = getSampleStyleSheet()["BodyText"]

    def make(name, **kw):
        kw.setdefault("fontName", font)
        return ParagraphStyle(name, parent=base, **kw)

    return {
        "name": make("Name", fontName=bold, fontSize=24 if on_band else 26,
                     leading=30, alignment=header_align, spaceAfter=2,
                     textColor=colors.white if on_band else accent),
        "headline": make("Headline", fontSize=12, leading=15,
                         alignment=header_align, spaceAfter=3,
                         textColor=colors.HexColor("#e5e7eb" if on_band else "#444444")),
        "contact": make("Contact", fontSize=9.5, leading=13,
                        alignment=header_align, spaceAfter=2,
                        textColor=colors.white if on_band else colors.HexColor("#333333")),
        "section": make("Section", fontName=bold, fontSize=11.5, leading=14,
                        textColor=accent, spaceBefore=0, spaceAfter=2,
                        alignment=TA_CENTER if theme["heading"] == "center" else TA_LEFT),
        "entry": make("Entry", fontSize=10.5, leading=14),
        "right": make("Right", fontSize=9.5, leading=14, alignment=TA_RIGHT,
                      textColor=colors.HexColor("#555555")),
        "body": make("Body", fontSize=10, leading=14),
        "bullet": make("Bullet", fontSize=10, leading=13.5, leftIndent=12,
                       bulletIndent=2),
    }


def _header(data, styles, theme):
    """Name, headline, and a clear contact block (email, phone, location, links)."""
    accent = colors.HexColor(theme["accent"])
    on_band = theme["header"] == "band"
    items = [Paragraph(_safe(data["name"]), styles["name"])]

    if data.get("headline"):
        items.append(Paragraph(_safe(data["headline"]), styles["headline"]))

    contact = [_safe(x) for x in
               (data.get("email"), data.get("phone"), data.get("location")) if x]
    if contact:
        items.append(Paragraph(" &nbsp;|&nbsp; ".join(contact), styles["contact"]))

    link_color = "#dbeafe" if on_band else "#2563eb"
    links = [_link(u.strip(), link_color)
             for u in data.get("links", "").split(",") if u.strip()]
    if links:
        items.append(Paragraph(" &nbsp;|&nbsp; ".join(links), styles["contact"]))

    if on_band:
        band = Table([[items]], colWidths=[FRAME_WIDTH], hAlign="LEFT")
        band.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), accent),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return [band]
    return items + [HRFlowable(width="100%", color=accent, thickness=1.5,
                               spaceBefore=4)]


def _heading(title, styles, theme):
    accent = colors.HexColor(theme["accent"])
    kind = theme["heading"]
    label = Paragraph(_safe(title.upper()), styles["section"])

    if kind == "bar":
        row = Table([["", label]], colWidths=[3, FRAME_WIDTH - 3], hAlign="LEFT")
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), accent),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        parts = [Spacer(1, 10), row, Spacer(1, 4)]
    elif kind == "center":
        parts = [Spacer(1, 10), label,
                 HRFlowable(width="30%", color=accent, thickness=0.8,
                            hAlign="CENTER", spaceAfter=4)]
    else:
        parts = [Spacer(1, 10), label,
                 HRFlowable(width="100%", color=accent, thickness=0.6,
                            spaceAfter=4)]

    for part in parts:  # never leave a heading alone at the bottom of a page
        part.keepWithNext = True
    return parts


def _entry_row(left, right, styles):
    """A line with text on the left and a right-aligned date or year."""
    table = Table(
        [[Paragraph(left, styles["entry"]), Paragraph(right, styles["right"])]],
        colWidths=[FRAME_WIDTH * 0.74, FRAME_WIDTH * 0.26],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    table.keepWithNext = True
    return table


def _bullets(text, styles):
    lines = [ln.strip(" -•\t") for ln in (text or "").splitlines()]
    return [Paragraph(_safe(ln), styles["bullet"], bulletText="•")
            for ln in lines if ln]


def _comma_list(text):
    return [item.strip() for item in (text or "").split(",") if item.strip()]


def build_resume_pdf(data, theme_key="classic"):
    """Return a BytesIO containing the finished PDF."""
    theme = THEMES.get(theme_key, THEMES["classic"])
    styles = _styles(theme)
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN,
        title=f"{data['name']} - Resume", author=data["name"],
    )

    story = _header(data, styles, theme)

    if data.get("summary"):
        story += _heading("Summary", styles, theme)
        story.append(Paragraph(_safe(data["summary"]), styles["body"]))

    skills = _comma_list(data.get("skills"))
    if skills:
        story += _heading("Skills", styles, theme)
        story.append(Paragraph(_safe(" • ".join(skills)), styles["body"]))

    if data.get("experience"):
        story += _heading("Experience", styles, theme)
        for job in data["experience"]:
            left = f"<b>{_safe(job['role'])}</b>"
            if job["company"]:
                left += f", {_safe(job['company'])}"
            story.append(_entry_row(left, _safe(job["dates"]), styles))
            story += _bullets(job["details"], styles)
            story.append(Spacer(1, 4))

    if data.get("projects"):
        story += _heading("Projects", styles, theme)
        for proj in data["projects"]:
            story.append(_entry_row(f"<b>{_safe(proj['title'])}</b>", "", styles))
            if proj["link"]:
                story.append(Paragraph(_link(proj["link"]), styles["bullet"]))
            story += _bullets(proj["description"], styles)
            story.append(Spacer(1, 4))

    if data.get("education"):
        story += _heading("Education", styles, theme)
        for edu in data["education"]:
            left = f"<b>{_safe(edu['degree'])}</b>"
            if edu["school"]:
                left += f", {_safe(edu['school'])}"
            story.append(_entry_row(left, _safe(edu["year"]), styles))
            story.append(Spacer(1, 3))

    if data.get("certificates"):
        story += _heading("Certifications", styles, theme)
        for cert in data["certificates"]:
            left = f"<b>{_safe(cert['name'])}</b>"
            if cert["issuer"]:
                left += f", {_safe(cert['issuer'])}"
            story.append(_entry_row(left, _safe(cert["year"]), styles))
            story.append(Spacer(1, 3))

    languages = _comma_list(data.get("languages"))
    if languages:
        story += _heading("Languages", styles, theme)
        story.append(Paragraph(_safe(" • ".join(languages)), styles["body"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
