# sre_core/pdf_report.py
from __future__ import annotations

import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Dict, List, Tuple

from fpdf import FPDF

from .constants import LEVELS
from .plotting import figure_to_image
from .gauges import stage_completion_from, make_semi_donut

# Replace glyphs that FPDF can't render in Latin-1
REPLACEMENTS = {"—": "-", "–": "-", "\u00A0": " "}

def _safe(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _save_fig_as_png(fig) -> str:
    """Save a Matplotlib Figure to a temp PNG; return path."""
    pil_img, _ = figure_to_image(fig)
    tmp = NamedTemporaryFile(delete=False, suffix=".png")
    pil_img.save(tmp.name)
    tmp.close()
    return tmp.name


def _render_stage_clocks(pdf: FPDF,
                         maturity_items: List[dict],
                         responses: Dict[str, Dict[str, str]]) -> None:
    """
    Render 'Stage Completion Overview' clocks under the radar diagrams.
    Uses Plotly->PNG via kaleido. If kaleido is missing, we silently skip.
    """
    try:
        completion = stage_completion_from(maturity_items, responses)
        if not completion:
            return

        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, _safe("Stage Completion Overview"), ln=True)
        pdf.set_font("Arial", size=9)
        pdf.cell(
            0, 6,
            _safe("% Completed across all capabilities and levels in the stage."),
            ln=True,
        )
        pdf.ln(2)

        # Layout grid
        col_w = 45     # horizontal step between clocks
        img_w = 28     # clock image width
        left = 18      # left margin start
        cols = 4

        x = left
        row_y = pdf.get_y()
        used_tmp: List[str] = []

        for i, (stage, pct) in enumerate(completion.items()):
            # Create gauge and export to PNG (requires kaleido)
            fig = make_semi_donut(stage, pct)
            png = NamedTemporaryFile(delete=False, suffix=".png")
            png.write(fig.to_image(format="png", width=240, height=240, scale=2))
            png.flush(); png.close()
            used_tmp.append(png.name)

            # Place image
            pdf.image(png.name, x=x, y=row_y, w=img_w)
            # Caption under each donut
            pdf.set_xy(x, row_y + img_w + 2)
            pdf.set_font("Arial", size=9)
            pdf.cell(img_w, 5, _safe(stage), align="C")

            # Move to next column / row
            if (i + 1) % cols == 0:
                row_y += img_w + 12
                x = left
                pdf.set_xy(x, row_y)
            else:
                x += col_w
                pdf.set_xy(x, row_y)

        # Cleanup temp images
        for p in used_tmp:
            try:
                os.remove(p)
            except Exception:
                pass

        pdf.ln(8)

    except Exception:
        # If kaleido is not available or anything fails, skip gauges gracefully
        pdf.ln(2)


def generate_pdf(
    product: str,
    maturity_items: List[dict],
    responses: Dict[str, Dict[str, str]],
    fig_stage,
    fig_cap,
):
    """
    Build the PDF exactly as before, but with the Stage Completion clocks
    inserted just under the radar diagrams. Everything else stays intact.
    Returns a NamedTemporaryFile handle.
    """
    # Save radar images from Matplotlib figures (temp files; /tmp is writable)
    stage_png = _save_fig_as_png(fig_stage)
    cap_png = _save_fig_as_png(fig_cap)

    # Build description lookup for prose sections
    desc_map = {
        (i["Stage"], i["Capability"]): {lvl: i[lvl] for lvl in LEVELS}
        for i in maturity_items
    }

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Header (keep original format) ---
    pdf.set_font("Arial", size=14, style="B")
    pdf.cell(0, 10, txt=_safe(f"SRE Maturity Report for: {product}"), ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=_safe(f"Generated: {datetime.utcnow():%Y-%m-%d %H:%M} UTC"), ln=True, align="C")
    pdf.ln(5)

    # --- Diagrams first (keep same placement logic) ---
    pdf.image(stage_png, x=15, w=180)
    pdf.ln(5)
    pdf.image(cap_png, x=15, w=180)

    # --- NEW: Stage Completion Overview (under the radars) ---
    _render_stage_clocks(pdf, maturity_items, responses)

    # Continue exactly as before
    pdf.add_page()

    # Group by Stage/Capability from maturity_items (source of truth)
    from collections import OrderedDict
    stages = OrderedDict()
    for i in maturity_items:
        stages.setdefault(i["Stage"], set()).add(i["Capability"])

    def section(title: str, keep: List[str]) -> None:
        pdf.set_font("Arial", size=12, style="B")
        pdf.cell(0, 8, txt=_safe(title), ln=True)
        pdf.ln(2)

        any_rows = False
        for stage, caps in stages.items():
            stage_printed = False
            for cap in sorted(caps):
                cap_resp = responses.get(cap, {})
                lines: List[Tuple[str, str, str]] = []
                for lvl in LEVELS:
                    status = cap_resp.get(lvl, "Not achieved")
                    if status in keep:
                        desc = desc_map.get((stage, cap), {}).get(lvl, "")
                        lines.append((lvl, status, desc))
                if lines:
                    any_rows = True
                    if not stage_printed:
                        pdf.set_font("Arial", size=11, style="B")
                        pdf.cell(0, 6, txt=_safe(stage), ln=True)
                        stage_printed = True
                    pdf.set_font("Arial", size=10, style="B")
                    pdf.cell(0, 6, txt=_safe(f"{cap}:"), ln=True)
                    pdf.set_font("Arial", size=10)
                    for lvl, stt, ds in lines:
                        # width=0 expands to page width; _safe avoids long glyph issues
                        pdf.multi_cell(0, 5, _safe(f"    {lvl} - {stt}: {ds};"))
                    pdf.ln(1)
            if stage_printed:
                pdf.ln(1)

        if not any_rows:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, txt="(none)", ln=True)

        pdf.ln(2)

    section("Completed", ["Completed"])
    section("Partially Achieved", ["Partially achieved"])
    section("Not Achieved", ["Not achieved"])

    # Write PDF and cleanup temp radar images
    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    tmp.seek(0)

    for p in (stage_png, cap_png):
        try:
            os.remove(p)
        except Exception:
            pass

    return tmp
