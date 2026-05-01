"""Generate `docs/agentos-datasheet.pdf` — a 1-2 page brochure designed for
LinkedIn / Twitter / cold email when someone asks "what is AgentOS?" without
wanting to read 4 docs. Layout: cover with positioning + value props, second
page with stack table + a deploy diagram + getting-started snippet.

Run:
    python scripts/generate_datasheet.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#2563eb")
SOFT = colors.HexColor("#1e293b")
SUBTLE = colors.HexColor("#475569")
LINE = colors.HexColor("#e2e8f0")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=ACCENT,
            spaceAfter=4,
        ),
        "tagline": ParagraphStyle(
            "TAG",
            parent=base["Heading2"],
            fontName="Helvetica",
            fontSize=14,
            textColor=SOFT,
            spaceAfter=18,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=SOFT,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BODY",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=SOFT,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "SMALL",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=SUBTLE,
        ),
        "code": ParagraphStyle(
            "CODE",
            parent=base["Code"],
            fontName="Courier",
            fontSize=9,
            leading=12,
            textColor=SOFT,
            backColor=colors.HexColor("#f8fafc"),
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "FOOTER",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            textColor=SUBTLE,
            alignment=TA_CENTER,
        ),
    }


def _value_prop_table(s: dict) -> Table:
    rows = [
        [
            Paragraph("<b>Multi-agente con razonamiento visible</b>", s["small"]),
            Paragraph(
                "router → researcher → analyst → writer. Cada paso emite SSE "
                "y la UI lo muestra en vivo.",
                s["small"],
            ),
        ],
        [
            Paragraph("<b>Failover entre 3 LLMs</b>", s["small"]),
            Paragraph(
                "Groq → OpenRouter → Gemini con circuit breaker. Un proveedor "
                "caído no rompe la app.",
                s["small"],
            ),
        ],
        [
            Paragraph("<b>RAG + Web search por agente</b>", s["small"]),
            Paragraph(
                "Conectá tus documentos (pgvector/FAISS) y/o búsqueda web "
                "(DuckDuckGo) a la pipeline de razonamiento.",
                s["small"],
            ),
        ],
        [
            Paragraph("<b>NL → SQL sobre tu DB</b>", s["small"]),
            Paragraph(
                "PG/MySQL/SQLite. SafeQueryExecutor bloquea DML y limita filas. "
                "Pregunta en lenguaje natural, devuelve SQL + resultados.",
                s["small"],
            ),
        ],
        [
            Paragraph("<b>Universal file adapter</b>", s["small"]),
            Paragraph(
                "PDF · DOCX · XLSX · CSV · JSON · MD · HTML · TXT · "
                "Parquet → texto + tabla normalizado.",
                s["small"],
            ),
        ],
        [
            Paragraph("<b>Deploy 100% gratis</b>", s["small"]),
            Paragraph(
                "Vercel (frontends) + Koyeb (backends) + Supabase (DB). "
                "30 minutos del repo a producción.",
                s["small"],
            ),
        ],
    ]
    table = Table(rows, colWidths=[1.9 * inch, 4.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _stack_table(s: dict) -> Table:
    rows = [
        ["Capa", "Tecnologías"],
        ["Frontends", "SvelteKit · Next.js 15 · Nuxt 3 (Tailwind v4 · TanStack Query)"],
        ["Estado UI", "Svelte runes · Zustand · Pinia"],
        ["Backend principal", "FastAPI + Pydantic + sse-starlette"],
        ["Backend alternativo", "Go (Gin) · Express · NestJS"],
        ["Agentes", "LangGraph 0.3 (DAG) + CrewAI 0.100 (crews)"],
        ["LLMs", "Groq · OpenRouter (`:free`) · Gemini Flash"],
        ["RAG", "sentence-transformers (MiniLM-L6-v2) + FAISS / pgvector"],
        ["Reportes", "ReportLab (default) · WeasyPrint (opcional)"],
        ["DB", "Supabase (Postgres + pgvector + PostGIS + Auth)"],
    ]
    t = Table(rows, colWidths=[1.6 * inch, 4.8 * inch])
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), SOFT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, ACCENT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def _deploy_table(s: dict) -> Table:
    rows = [
        ["Componente", "Plataforma", "Free tier"],
        ["3 frontends", "Vercel", "100 GB / 100 deploys día"],
        ["FastAPI + Go API", "Koyeb", "1 nano · 512 MB RAM"],
        ["Postgres + pgvector + PostGIS", "Supabase", "500 MB · 2 proyectos"],
        ["Bot Telegram", "Koyeb worker", "1 nano"],
        ["PocketBase (opcional)", "PocketHost", "1 instancia"],
    ]
    t = Table(rows, colWidths=[2.4 * inch, 1.6 * inch, 2.4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), SOFT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, ACCENT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build_datasheet(output: Path) -> int:
    s = _styles()
    doc = SimpleDocTemplate(
        str(output),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="AgentOS — Datasheet",
        author="AgentOS",
    )

    story: list = []

    # ── Cover ──
    story.append(Paragraph("AgentOS", s["h1"]))
    story.append(
        Paragraph(
            "Plataforma multi-agente con failover automático. "
            "Construí apps con IA en horas, no semanas.",
            s["tagline"],
        )
    )

    story.append(Paragraph("¿Para quién es?", s["h2"]))
    story.append(
        Paragraph(
            "Equipos de hackathon, startups que validan ideas con IA, consultores que "
            "entregan prototipos, y equipos internos que prefieren no atarse a un "
            "SaaS pago. Si tu app cae en el patrón <b>el usuario pregunta — la IA "
            "razona con tus datos — devuelve una respuesta</b>, AgentOS te ahorra el "
            "70% del trabajo inicial.",
            s["body"],
        )
    )

    story.append(Paragraph("¿Qué te da listo?", s["h2"]))
    story.append(_value_prop_table(s))

    story.append(Paragraph("Estado actual", s["h2"]))
    story.append(
        Paragraph(
            "66+ tests verdes (LLM · agentes · RAG · DB · notifications · files). "
            "CI corre la suite completa + 3-frontend matrix en cada PR. CD "
            "auto-despliega Svelte / Next / Vue a Vercel y FastAPI / Go a Koyeb "
            "en cada merge a main.",
            s["body"],
        )
    )

    story.append(PageBreak())

    # ── Page 2 ──
    story.append(Paragraph("Stack técnico", s["h2"]))
    story.append(_stack_table(s))

    story.append(Paragraph("Despliegue gratuito", s["h2"]))
    story.append(_deploy_table(s))

    story.append(Paragraph("Empezar en 5 comandos", s["h2"]))
    story.append(
        Paragraph(
            "git clone &lt;repo&gt; &amp;&amp; cd agentos<br/>"
            "cp .env.example .env  <font color='#94a3b8'># pega GROQ_API_KEY (gratis)</font><br/>"
            "pnpm install<br/>"
            "pip install -e packages/llm packages/agents packages/rag packages/files services/api<br/>"
            "cd services/api &amp;&amp; uvicorn app.main:app --reload",
            s["code"],
        )
    )
    story.append(
        Paragraph(
            "En otra terminal: <b>pnpm preview</b> abre un selector visual para "
            "elegir entre los 3 frontends (Svelte 5173 · Next 3000 · Nuxt 3001). "
            "Tres temas (Slate / Indigo / Ivory) se intercambian al toque, en "
            "cualquiera de los tres.",
            s["body"],
        )
    )

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "MIT · github.com/agentos · documentación completa en español "
            "(<b>docs/es/</b>) y en inglés (<b>docs/</b>).",
            s["footer"],
        )
    )

    doc.build(story)
    return output.stat().st_size


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    output = repo / "docs" / "agentos-datasheet.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    size = build_datasheet(output)
    print(f"AgentOS datasheet -> {output.relative_to(repo)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
