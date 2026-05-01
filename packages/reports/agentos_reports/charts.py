import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def bar_chart(labels: list[str], values: list[float], title: str = "") -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color="#5c7cfa")
    ax.set_title(title)
    plt.tight_layout()
    return _fig_to_base64(fig)


def line_chart(x: list, y: list, title: str = "", xlabel: str = "", ylabel: str = "") -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, color="#20c997", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    return _fig_to_base64(fig)


def _fig_to_base64(fig) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"
