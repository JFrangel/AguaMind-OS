def render_pdf(template_name: str, data: dict, output_path: str | None = None) -> bytes:
    """Render `data` through `template_name` (Jinja) and return PDF bytes.

    Tries WeasyPrint first (best CSS fidelity for HTML reports). Falls back
    to ReportLab when WeasyPrint can't load its native deps (typical on
    Windows where GTK isn't installed). The fallback path is self-contained
    in pure Python so the boilerplate works out of the box.

    Pass `output_path` to also write to disk.
    """
    from .generator import render_pdf as _render_pdf

    return _render_pdf(template_name, data, output_path)


def render_response_pdf(
    *, title: str, content: str, subtitle: str | None = None, output_path: str | None = None
) -> bytes:
    """Convenience for the chat "export this answer" flow. Uses ReportLab
    directly so it never hits the GTK requirement and produces a clean
    one-column PDF with markdown-rendered body."""
    from .reportlab_renderer import render_response

    return render_response(title=title, content=content, subtitle=subtitle, output_path=output_path)


__all__ = ["render_pdf", "render_response_pdf"]
