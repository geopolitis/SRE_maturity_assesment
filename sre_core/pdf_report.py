from __future__ import annotations
from typing import Dict, List
from datetime import datetime
from tempfile import NamedTemporaryFile
from fpdf import FPDF
import re

from .constants import LEVELS
from .plotting import figure_to_image
from .gauges import grid_from_completion, ring_maturity_by_stage, build_status_map  
REPLACEMENTS = {"—": "-", "–": "-", "\u00A0": " "}
def _safe(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")

def _compute_stage_completion(maturity_items: List[dict], responses: Dict[str, Dict[str, str]]) -> Dict[str, float]:
    by_stage = {}
    for it in maturity_items:
        by_stage.setdefault(it["Stage"], []).append(it)
    out: Dict[str, float] = {}
    for stage, caps in by_stage.items():
        total = done = 0
        for it in caps:
            cap_res = responses.get(it["Capability"], {})
            for lvl in LEVELS:
                total += 1
                if cap_res.get(lvl, "Not achieved") == "Completed":
                    done += 1
        out[stage] = (done / total) if total else 0.0
    return out

def _soft_break_long_tokens(text: str, limit: int = 50) -> str:
    """Insert spaces into very long unbroken tokens to avoid FPDF width errors."""
    def breaker(match: re.Match) -> str:
        s = match.group(0)
        return " ".join(s[i:i+limit] for i in range(0, len(s), limit))
    # Break any sequence of non-space characters longer than `limit`
    return re.sub(r"\S{%d,}" % limit, breaker, text)

def _wrap_multicell(pdf: FPDF, txt: str, h: float = 5):
    """Write wrapped text using the full effective page width.

    Avoids FPDFException when current X is near the right margin by
    always resetting X and passing an explicit width (epw).
    Also inserts soft breaks for long tokens.
    """
    safe = _safe(txt or "")
    safe = _soft_break_long_tokens(safe, limit=48)
    try:
        w = pdf.epw  # effective page width (fpdf2)
    except Exception:
        w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(w, h, safe)

def generate_pdf(
    product: str,
    maturity_items: List[dict],
    responses: Dict[str, Dict[str, str]],
    fig_stage,
    fig_cap,
):
    img_stage, _ = figure_to_image(fig_stage); img_stage.save("radar_stage.png")
    img_cap, _   = figure_to_image(fig_cap);   img_cap.save("radar_capability.png")

    desc_map = {
        (i["Stage"], i["Capability"]): {lvl: i.get(lvl, "") for lvl in LEVELS}
        for i in maturity_items
    }

    pdf = FPDF()
    margin = 15
    pdf.set_auto_page_break(auto=False, margin=margin)

    # -------- Page 1: Degree of Implementation (Ring) --------
    pdf.add_page()
    pdf.set_font("Arial", size=14, style="B")
    pdf.cell(0, 10, txt=_safe(f"SRE Maturity Report for: {product}"), ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=_safe(f"Generated: {datetime.now():%Y-%m-%d %H:%M}"), ln=True, align="C")
    pdf.ln(8)

    # Build tri-state status for ring
    status_map = build_status_map(maturity_items, responses, LEVELS)

    # Create ring figure and embed
    by_stage = {}
    for it in maturity_items:
        by_stage.setdefault(it["Stage"], []).append(it)
    stages_order = sorted(by_stage.keys())
    label_overrides = {"Develop": 190, "Observe": 190, "Secure": 190, "Test": 190, "tests": 190, "Tests": 190}
    fig_ring = ring_maturity_by_stage(
        stages=stages_order,
        levels=LEVELS,
        status_map=status_map,
        label_rotation_overrides=label_overrides,
        figsize=(9, 9),
    )
    ring_img, _ = figure_to_image(fig_ring)
    ring_img.save("ring_stage.png")
    usable_w = pdf.w - 2 * margin
    pdf.image("ring_stage.png", x=margin, w=usable_w)

    # -------- Page 2: Two radars stacked (full width) --------
    pdf.add_page()
    # compute layout
    usable_w = pdf.w - 2 * margin
    usable_h = pdf.h - 2 * margin
    gap = 8

    # Helper: compute placed heights for a given width
    def _img_height_at_width(path: str, width: float) -> float:
        try:
            from PIL import Image
            w_px, h_px = Image.open(path).size
            if w_px == 0:
                return width  # degenerate fallback
            return (h_px / w_px) * width
        except Exception:
            return width

    # Choose a width that allows both radars to fit vertically
    w_try = usable_w
    h1 = _img_height_at_width("radar_stage.png", w_try)
    h2 = _img_height_at_width("radar_capability.png", w_try)
    total_h = h1 + h2 + gap
    if total_h > usable_h:
        scale = usable_h / total_h
        w_try *= scale
        h1 *= scale
        h2 *= scale

    x = margin + (usable_w - w_try) / 2.0  # centered
    y = margin
    pdf.image("radar_stage.png", x=x, y=y, w=w_try)
    y += h1 + gap
    pdf.image("radar_capability.png", x=x, y=y, w=w_try)

    # -------- Page 3: Donuts grid --------
    pdf.add_page()
    completion = _compute_stage_completion(maturity_items, responses)
    if completion:
        try:
            fig_clocks, _ = grid_from_completion(completion, cols=5 if len(completion) >= 7 else 3, show=False)
            clocks_img, _ = figure_to_image(fig_clocks)
            clocks_img.save("stage_clocks.png")
            pdf.image("stage_clocks.png", x=margin, y=margin, w=usable_w)
        except Exception:
            pass

    # -------- Textual sections (restored content) --------
    # Enable auto page breaks for narrative content
    pdf.set_auto_page_break(auto=True, margin=margin)
    pdf.add_page()

    from collections import OrderedDict
    stages = OrderedDict()
    for i in maturity_items:
        stages.setdefault(i["Stage"], set()).add(i["Capability"])

    def section(title, keep_statuses):
        pdf.set_font("Arial", size=12, style="B")
        pdf.cell(0, 8, txt=_safe(title), ln=True)
        pdf.ln(2)
        any_rows = False

        for stage, caps in stages.items():
            stage_printed = False
            for cap in sorted(caps):
                cap_resp = responses.get(cap, {})
                lines = []
                for lvl in LEVELS:
                    stt = cap_resp.get(lvl, "Not achieved")
                    if stt in keep_statuses:
                        ds = desc_map.get((stage, cap), {}).get(lvl, "")
                        lines.append((lvl, stt, ds))
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
                        _wrap_multicell(pdf, f"    {lvl} - {stt}: {ds}", h=5)
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

    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    tmp.seek(0)
    return tmp
