from collections import OrderedDict
from .constants import LEVELS

def markdown_report(product: str, maturity_items, responses: dict) -> str:
    def md_line(s): return s + "  \n"  # hard line break
    stages = OrderedDict()
    for item in maturity_items:
        stage, cap = item["Stage"], item["Capability"]
        stages.setdefault(stage, OrderedDict()).setdefault(cap, [])
        ans = responses.get(cap, {})
        for lvl in LEVELS:
            status = ans.get(lvl, "Not achieved")
            desc = item[lvl]
            if status in ("Not achieved", "Partially achieved"):
                status = f"*{status}*"
            stages[stage][cap].append((lvl, status, desc))

    out = []
    out.append(md_line(f"# SRE Maturity Text Report for: {product}"))
    out.append("")

    # Completed
    out.append(md_line("## ✅ Completed (to celebrate):"))
    any_completed = False
    for stage, caps in stages.items():
        cap_lines = []
        for cap, triples in caps.items():
            completed = [(lvl, st, ds) for lvl, st, ds in triples if st == "Completed"]
            if completed:
                cap_lines.append((cap, completed))
        if cap_lines:
            any_completed = True
            out.append(md_line(f"### {stage}"))
            for cap, triples in cap_lines:
                out.append(md_line(f"**{cap}:**"))
                for lvl, st, ds in triples:
                    out.append(md_line(f"&nbsp;&nbsp;&nbsp;&nbsp;{lvl} — {st}: {ds};"))
                out.append("")
    if not any_completed:
        out.append(md_line("_Nothing completed yet._"))
        out.append("")

    # Needs work
    out.append(md_line("## 🛠 Needs Work (Not achieved or Partially achieved):"))
    any_needs = False
    for stage, caps in stages.items():
        cap_lines = []
        for cap, triples in caps.items():
            nw = [(lvl, st, ds) for lvl, st, ds in triples if "Not achieved" in st or "Partially" in st]
            if nw: cap_lines.append((cap, nw))
        if cap_lines:
            any_needs = True
            out.append(md_line(f"### {stage}"))
            for cap, triples in cap_lines:
                out.append(md_line(f"**{cap}:**"))
                for lvl, st, ds in triples:
                    out.append(md_line(f"&nbsp;&nbsp;&nbsp;&nbsp;{lvl} — {st}: {ds};"))
                out.append("")
    if not any_needs:
        out.append(md_line("_Everything is completed! 🎯_"))
    return "\n".join(out)
