# sre_core/gauges.py
from __future__ import annotations

import textwrap
from collections import OrderedDict
from typing import Dict, List
import plotly.graph_objects as go

from .constants import LEVELS


def wrap_label(label: str, width: int = 18) -> str:
    """Wrap long titles for compact display (Plotly annotations)."""
    return "<br>".join(textwrap.wrap(label, width=width)) if label else label


def stage_completion_for_product(
    product: str,
    maturity_items: List[dict],
    responses_all: Dict[str, Dict[str, Dict[str, str]]],
) -> Dict[str, float]:
    """Return 0..1 completion per Stage for the selected product."""
    prod_res = responses_all.get(product, {})
    return stage_completion_from(maturity_items, prod_res)


def stage_completion_from(
    maturity_items: List[dict],
    responses: Dict[str, Dict[str, str]],
) -> OrderedDict[str, float]:
    """Return 0..1 completion per Stage using a single product's responses."""
    by_stage: OrderedDict[str, List[dict]] = OrderedDict()
    for it in maturity_items:
        by_stage.setdefault(it["Stage"], []).append(it)

    out: OrderedDict[str, float] = OrderedDict()
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


def make_semi_donut(title: str, pct_float: float) -> go.Figure:
    """
    Semi-donut gauge built from layered pies.
    Matches the Visual Report look & feel.
    """
    pct = max(0.0, min(1.0, float(pct_float)))
    pct_val = round(pct * 100, 1)

    band_low = "#ffefef"    # 0–40
    band_mid = "#fff6db"    # 40–80
    band_high = "#edfbea"   # 80–100
    transparent = "rgba(0,0,0,0)"
    bar_color = "red" if pct < 0.4 else ("orange" if pct < 0.8 else "green")

    bg = go.Pie(
        values=[40, 40, 20, 100],  # sums to 200; last 100 is the hidden lower half
        rotation=180,
        hole=0.70,
        marker=dict(colors=[band_low, band_mid, band_high, transparent]),
        textinfo="none",
        hoverinfo="skip",
        sort=False,
        direction="clockwise",
        showlegend=False,
    )

    fg = go.Pie(
        values=[pct * 100, (1 - pct) * 100, 100],
        rotation=180,
        hole=0.70,
        marker=dict(colors=[bar_color, transparent, transparent]),
        textinfo="none",
        hoverinfo="skip",
        sort=False,
        direction="clockwise",
        showlegend=False,
    )

    fig = go.Figure(data=[bg, fg])
    fig.update_layout(
        height=230,
        margin=dict(t=38, b=8, l=8, r=8),
        annotations=[
            dict(
                text=wrap_label(title, 20),
                x=0.5, y=1.15, xref="paper", yref="paper",
                showarrow=False, align="center", font=dict(size=12),
            ),
            dict(
                text=f"{pct_val:g}%",
                x=0.5, y=0.48, xref="paper", yref="paper",
                showarrow=False, align="center", font=dict(size=20),
            ),
            dict(text="0",   x=0.05, y=0.08, xref="paper", yref="paper",
                 showarrow=False, font=dict(size=10, color="#555")),
            dict(text="50",  x=0.50, y=0.13, xref="paper", yref="paper",
                 showarrow=False, font=dict(size=10, color="#555")),
            dict(text="100", x=0.95, y=0.08, xref="paper", yref="paper",
                 showarrow=False, font=dict(size=10, color="#555")),
        ],
        showlegend=False,
    )
    return fig
