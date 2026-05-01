from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_pdf(template_name: str, data: dict, output_path: str | None = None) -> bytes:
    """Render template → HTML → PDF.

    The HTML pipeline is the same regardless of the backend; only the
    HTML→PDF step differs:

      * WeasyPrint (default): full CSS support, page breaks, charts, etc.
      * ReportLab fallback: triggered when WeasyPrint can't import its
        native libs (Windows without GTK). Produces a simpler-looking but
        usable PDF from the same data.
    """
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    html_content = template.render(**data)

    pdf_bytes = _html_to_pdf(html_content, data)

    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
    return pdf_bytes


def _html_to_pdf(html: str, data: dict) -> bytes:
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf()
    except (ImportError, OSError):
        # WeasyPrint unavailable (typical on Windows without GTK). Fall
        # back to ReportLab using the structured data we already have.
        from .reportlab_renderer import render_from_template_data

        return render_from_template_data(data)
