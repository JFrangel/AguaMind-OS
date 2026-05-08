#!/usr/bin/env python3
"""
WaterMind OS — Generador de PDF entregable hackathon UNIAJC 2026.

Convierte template.html + styles.css → WaterMind-OS-Hackathon-2026.pdf
usando WeasyPrint.

Uso:
    python docs/pdf/generate_pdf.py

Requisitos macOS:
    brew install pango cairo gdk-pixbuf libffi
    pip install weasyprint
"""

import ctypes
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML_FILE   = HERE / "template.html"
CSS_FILE    = HERE / "styles.css"
OUTPUT_FILE = HERE / "WaterMind-OS-Hackathon-2026.pdf"

# Pre-cargar libs (necesario en macOS Apple Silicon)
HOMEBREW_LIB = "/opt/homebrew/lib"
if os.path.isdir(HOMEBREW_LIB):
    os.environ["DYLD_LIBRARY_PATH"] = HOMEBREW_LIB
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = HOMEBREW_LIB
    for lib in [
        "libgobject-2.0.0.dylib",
        "libpango-1.0.0.dylib",
        "libpangoft2-1.0.0.dylib",
        "libharfbuzz.0.dylib",
        "libfontconfig.1.dylib",
    ]:
        path = os.path.join(HOMEBREW_LIB, lib)
        if os.path.isfile(path):
            try:
                ctypes.CDLL(path)
            except OSError:
                pass


def main() -> int:
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        print("✗ WeasyPrint no instalado. Ejecuta: pip install weasyprint")
        return 1

    if not HTML_FILE.exists():
        print(f"✗ No se encuentra: {HTML_FILE}")
        return 1

    print(f"⚙ Generando PDF desde {HTML_FILE.name}…")
    try:
        HTML(str(HTML_FILE)).write_pdf(
            str(OUTPUT_FILE),
            stylesheets=[CSS(str(CSS_FILE))],
        )
    except Exception as e:
        print(f"✗ Error al generar PDF: {e}")
        return 1

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"✓ PDF generado: {OUTPUT_FILE.name} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
