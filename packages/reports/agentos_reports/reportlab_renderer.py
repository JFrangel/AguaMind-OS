"""Pure-Python PDF renderer used when WeasyPrint isn't available.

The output won't match WeasyPrint pixel-for-pixel (no full CSS), but it's
clean, readable, and zero-config. Two entry points:

    render_response(title, content, subtitle?) → chat "export this answer"
    render_from_template_data(data)            → fallback for /reports/generate
"""
from __future__ import annotations

import io
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _styles():
    base = getSampleStyleSheet()
    accent = colors.HexColor("#2563eb")

    h1 = ParagraphStyle(
        "AOSHeading1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=accent,
        spaceAfter=14,
    )
    h2 = ParagraphStyle(
        "AOSHeading2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "AOSBody",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#212529"),
        alignment=TA_LEFT,
    )
    small = ParagraphStyle(
        "AOSSmall",
        parent=base["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=10,
    )
    code = ParagraphStyle(
        "AOSCode",
        parent=base["Code"],
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        backColor=colors.HexColor("#f3f4f6"),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=4,
        spaceAfter=8,
    )
    return {"h1": h1, "h2": h2, "body": body, "small": small, "code": code}


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline_md_to_rl(text: str) -> str:
    """Convert a single line of light markdown to ReportLab inline tags."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _BOLD.sub(r"<b>\1</b>", text)
    text = _ITAL.sub(r"<i>\1</i>", text)
    text = _CODE.sub(r'<font face="Courier" backColor="#f3f4f6">\1</font>', text)
    text = _LINK.sub(r'<link href="\2" color="#2563eb">\1</link>', text)
    return text


def _markdown_to_flowables(content: str, styles: dict) -> list:
    """Walk the markdown line-by-line, emitting Paragraphs/Tables for each
    construct. Supports headings, bullet/numbered lists, code fences, and
    GitHub-style tables. Anything else is treated as a paragraph.
    """
    lines = content.splitlines()
    flowables: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Code fence
        if stripped.startswith("```"):
            block: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code_text = "\n".join(block)
            safe = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            flowables.append(Paragraph(safe.replace("\n", "<br/>"), styles["code"]))
            continue

        # Heading
        if stripped.startswith("###"):
            flowables.append(Paragraph(_inline_md_to_rl(stripped.lstrip("#").strip()), styles["h2"]))
            i += 1
            continue
        if stripped.startswith("##") or stripped.startswith("# "):
            flowables.append(Paragraph(_inline_md_to_rl(stripped.lstrip("#").strip()), styles["h1"]))
            i += 1
            continue

        # Table (markdown pipe table). At least two rows: header + separator.
        if "|" in stripped and i + 1 < len(lines) and re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", lines[i + 1]):
            rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i]:
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(row)
                i += 1
            if len(rows) >= 2:
                rows.pop(1)  # drop separator
                flowables.append(_table(rows))
                flowables.append(Spacer(1, 6))
            continue

        # Bullet / numbered list
        if re.match(r"^\s*[-*]\s+", stripped) or re.match(r"^\s*\d+\.\s+", stripped):
            block_lines: list[str] = []
            while i < len(lines) and (
                re.match(r"^\s*[-*]\s+", lines[i].strip())
                or re.match(r"^\s*\d+\.\s+", lines[i].strip())
            ):
                item = re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i].strip())
                block_lines.append(f"• {_inline_md_to_rl(item)}")
                i += 1
            for bullet in block_lines:
                flowables.append(Paragraph(bullet, styles["body"]))
            flowables.append(Spacer(1, 4))
            continue

        # Blank line
        if not stripped:
            flowables.append(Spacer(1, 6))
            i += 1
            continue

        # Default paragraph (collect consecutive non-blank lines)
        para: list[str] = []
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        if para:
            flowables.append(Paragraph(_inline_md_to_rl(" ".join(para)), styles["body"]))
            flowables.append(Spacer(1, 4))
    return flowables


def _is_block_start(line: str) -> bool:
    s = line.strip()
    return (
        s.startswith("#")
        or s.startswith("```")
        or bool(re.match(r"^\s*[-*]\s+", s))
        or bool(re.match(r"^\s*\d+\.\s+", s))
    )


def _table(rows: list[list[str]]) -> Table:
    width = max(len(r) for r in rows)
    normalized = [r + [""] * (width - len(r)) for r in rows]
    table = Table(normalized, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#dee2e6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def render_response(
    *, title: str, content: str, subtitle: str | None = None, output_path: str | None = None
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=title,
    )
    styles = _styles()
    flow: list = [Paragraph(_inline_md_to_rl(title), styles["h1"])]
    if subtitle:
        flow.append(Paragraph(_inline_md_to_rl(subtitle), styles["small"]))
    flow.extend(_markdown_to_flowables(content, styles))
    doc.build(flow)
    pdf = buf.getvalue()
    if output_path:
        from pathlib import Path

        Path(output_path).write_bytes(pdf)
    return pdf


def render_from_template_data(data: dict) -> bytes:
    """Fallback path used when WeasyPrint is unavailable. Only handles the
    shapes our two stock templates produce: chat-response (`content`) and
    structured (`title` + `metrics` + `table_*`).
    """
    if data.get("content"):
        return render_response(
            title=data.get("title") or "AgentOS",
            subtitle=data.get("subtitle"),
            content=data["content"],
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, title=data.get("title") or "Report")
    styles = _styles()
    flow: list = [Paragraph(_inline_md_to_rl(data.get("title") or "Report"), styles["h1"])]
    if data.get("description"):
        flow.append(Paragraph(_inline_md_to_rl(str(data["description"])), styles["body"]))
        flow.append(Spacer(1, 6))

    metrics = data.get("metrics") or []
    if metrics:
        rows = [["Métrica", "Valor"]] + [[str(m.get("label", "")), str(m.get("value", ""))] for m in metrics]
        flow.append(_table(rows))
        flow.append(Spacer(1, 10))

    cols = data.get("table_columns") or []
    rows_data = data.get("table_data") or []
    if cols and rows_data:
        rows = [cols] + [[str(r.get(c, "")) for c in cols] for r in rows_data]
        flow.append(_table(rows))

    if data.get("summary"):
        flow.append(Paragraph("Resumen", styles["h2"]))
        flow.append(Paragraph(_inline_md_to_rl(str(data["summary"])), styles["body"]))

    doc.build(flow)
    return buf.getvalue()
