from __future__ import annotations
from typing import Dict, List
from datetime import datetime
from tempfile import NamedTemporaryFile
from fpdf import FPDF

from .constants import LEVELS
from .plotting import figure_to_image
from .gauges import grid_from_completion, ring_maturity_by_stage  
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

def _wrap_multicell(pdf: FPDF, txt: str, h: float = 5):
    max_chars = 150
    if len(txt) <= max_chars:
        pdf.multi_cell(0, h, _safe(txt))
        return
    start = 0
    while start < len(txt):
        pdf.multi_cell(0, h, _safe(txt[start:start+max_chars]))
        start += max_chars

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
    pdf.ln(3)

    # Build tri-state status for ring
    by_stage = {}
    for it in maturity_items:
        by_stage.setdefault(it["Stage"], []).append(it)
    status_map = {}
    for stage, caps in by_stage.items():
        for lvl in LEVELS:
            total = 0
            completed = 0
            partial = 0
            for it in caps:
                cap_res = (responses or {}).get(it["Capability"], {}) or {}
                stt = cap_res.get(lvl, "Not achieved")
                total += 1
                if stt == "Completed":
                    completed += 1
                elif stt == "Partially achieved":
                    partial += 1
            if total and completed == total:
                status_map[(stage, lvl)] = "completed"
            elif (completed > 0) or (partial > 0):
                status_map[(stage, lvl)] = "partial"
            else:
                status_map[(stage, lvl)] = "not"

    # Create ring figure and embed
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

    # -------- Page 2: Two radars on top, donuts bottom --------
    pdf.add_page()
    # compute layout
    usable_w = pdf.w - 2 * margin
    usable_h = pdf.h - 2 * margin
    gap = 5
    half_w = (usable_w - gap) / 2.0
    top_h = half_w  # assume square radars; height ~ width
    bottom_y = margin + top_h + 6  # start of bottom area

    # stage radar (left)
    pdf.image("radar_stage.png", x=margin, y=margin, w=half_w)
    # capability radar (right)
    pdf.image("radar_capability.png", x=margin + half_w + gap, y=margin, w=half_w)

    # Donuts grid at bottom
    completion = _compute_stage_completion(maturity_items, responses)
    if completion:
        try:
            fig_clocks, _ = grid_from_completion(completion, cols=5 if len(completion) >= 7 else 3, show=False)
            clocks_img, _ = figure_to_image(fig_clocks)
            clocks_img.save("stage_clocks.png")
            pdf.image("stage_clocks.png", x=margin, y=bottom_y, w=usable_w)
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
                        _wrap_multicell(pdf, f"    {lvl} - {stt}: {ds};", h=5)
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
