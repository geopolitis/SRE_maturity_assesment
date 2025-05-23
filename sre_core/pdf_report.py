from fpdf import FPDF
from datetime import datetime
from tempfile import NamedTemporaryFile
from .constants import LEVELS
from .plotting import figure_to_image

REPLACEMENTS = {"—": "-", "–": "-", "\u00A0": " "}
def _safe(s: str) -> str:
    if not isinstance(s, str): s = str(s)
    for k, v in REPLACEMENTS.items(): s = s.replace(k, v)
    return s.encode("latin-1","ignore").decode("latin-1")

def generate_pdf(product, maturity_items, responses, fig_stage, fig_cap):
    # save images from figs
    img_stage, _ = figure_to_image(fig_stage); img_stage.save("radar_stage.png")
    img_cap, _ = figure_to_image(fig_cap);     img_cap.save("radar_capability.png")

    # build description lookup
    desc_map = {(i["Stage"], i["Capability"]): {lvl: i[lvl] for lvl in LEVELS} for i in maturity_items}

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=14, style="B")
    pdf.cell(0, 10, txt=_safe(f"SRE Maturity Report for: {product}"), ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, txt=_safe(f"Generated: {datetime.now():%Y-%m-%d %H:%M}"), ln=True, align="C")
    pdf.ln(5)

    # diagrams first
    pdf.image("radar_stage.png", x=15, w=180); pdf.ln(5)
    pdf.image("radar_capability.png", x=15, w=180)
    pdf.add_page()

    # group by Stage/Capability from maturity_items (source of truth)
    from collections import OrderedDict
    stages = OrderedDict()
    for i in maturity_items:
        stages.setdefault(i["Stage"], set()).add(i["Capability"])

    def section(title, keep):
        pdf.set_font("Arial", size=12, style="B")
        pdf.cell(0, 8, txt=_safe(title), ln=True); pdf.ln(2)
        any_rows = False
        for stage, caps in stages.items():
            stage_printed = False
            for cap in sorted(caps):
                cap_resp = responses.get(cap, {})
                lines = []
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
                    for lvl, st, ds in lines:
                        pdf.multi_cell(0, 5, _safe(f"    {lvl} - {st}: {ds};"))
                    pdf.ln(1)
            if stage_printed: pdf.ln(1)
        if not any_rows:
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, txt="(none)", ln=True)
        pdf.ln(2)

    section("Completed", ["Completed"])
    section("Partially Achieved", ["Partially achieved"])
    section("Not Achieved", ["Not achieved"])

    tmp = NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name); tmp.seek(0)
    return tmp
