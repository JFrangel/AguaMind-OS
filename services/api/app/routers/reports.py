from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from agentos_reports import render_pdf, render_response_pdf

router = APIRouter()


class ReportRequest(BaseModel):
    """Either supply a structured report (template + metrics + table) or a
    free-form chat response (`content`). The router picks the right path:
    explicit `template` always wins; otherwise when only `content` is set
    we use the ReportLab response renderer directly (no WeasyPrint, no GTK
    requirement — works on Windows out of the box).
    """

    template: str | None = None
    title: str = "AgentOS — Respuesta"
    subtitle: str | None = None
    content: str | None = None
    description: str = ""
    summary: str = ""
    metrics: list[dict] = []
    table_columns: list[str] = []
    table_data: list[dict] = []


@router.post("/generate")
async def generate_report(body: ReportRequest):
    if body.template is None and body.content:
        pdf_bytes = render_response_pdf(
            title=body.title,
            subtitle=body.subtitle,
            content=body.content,
        )
    else:
        template = body.template or "report.html"
        pdf_bytes = render_pdf(template, body.model_dump())

    safe_name = (body.title or "agentos").replace(" ", "_")[:60]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.pdf"'},
    )
