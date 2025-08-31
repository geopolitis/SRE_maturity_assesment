import os
import sys
import io
import numpy as np

# Ensure project root is on path for importing sre_core
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sre_core.constants import LEVELS
from sre_core.gauges import grid_from_completion, ring_maturity_by_stage, build_status_map
from sre_core.plotting import figure_to_image
from sre_core import scoring, pdf_report


def sample_data():
    maturity_items = [
        {"Stage": "Build", "Capability": "CI", LEVELS[0]: "", LEVELS[1]: "", LEVELS[2]: "", LEVELS[3]: "", LEVELS[4]: ""},
        {"Stage": "Deploy", "Capability": "CD", LEVELS[0]: "", LEVELS[1]: "", LEVELS[2]: "", LEVELS[3]: "", LEVELS[4]: ""},
    ]
    responses_all = {
        "ProductA": {
            "CI": {LEVELS[0]: "Completed", LEVELS[1]: "Partially achieved"},
            "CD": {LEVELS[0]: "Not achieved", LEVELS[1]: "Completed"},
        }
    }
    return maturity_items, responses_all


def test_scoring_build_df():
    items, responses_all = sample_data()
    df = scoring.build_df(items, responses_all)
    assert not df.empty
    assert set(df["Product"]) == {"ProductA"}
    # score = sum sub-level scores across LEVELS; only specified levels contribute
    row_ci = df[df["Capability"] == "CI"].iloc[0]
    assert row_ci["Score"] >= 1.0  # Completed (1.0) + Partially (0.5)


def test_grid_from_completion():
    completion = {"Build": 0.6, "Deploy": 0.2}
    fig, axes = grid_from_completion(completion, cols=2, show=False)
    assert fig is not None
    # inspect first donut patches
    ax = axes[0][0]
    wedges = [p for p in ax.patches if hasattr(p, 'theta1')]
    assert len(wedges) >= 2
    bg = wedges[0]
    fill = wedges[1]
    # background is top semicircle
    assert round(bg.theta1) == 0 and round(bg.theta2) == 180
    # fill should end at 180 and start earlier based on pct (0.6 => span 108)
    assert round(fill.theta2) == 180
    assert round(fill.theta1) == 72  # 180-108


def test_ring_maturity_by_stage():
    stages = ["Build", "Deploy"]
    levels = LEVELS[:3]
    status_map = {("Build", levels[0]): "completed", ("Build", levels[1]): "partial"}
    fig = ring_maturity_by_stage(stages, levels, status_map=status_map, figsize=(4, 4))
    assert fig is not None
    ax = fig.axes[0]
    patches = ax.patches
    assert any(p.get_alpha() == 0.35 for p in patches)  # partial band
    assert any((p.get_alpha() is None or p.get_alpha() == 1.0) and \
               (hasattr(p, 'get_facecolor') and tuple(int(c*255) for c in p.get_facecolor()[:3])[:3] != (234,234,234))
               for p in patches)

    # Label alignment and overrides
    fig2 = ring_maturity_by_stage(stages, levels, status_map=status_map, figsize=(4,4))
    fig3 = ring_maturity_by_stage(stages, levels, status_map=status_map, figsize=(4,4), label_rotation_overrides={"Build": 10})
    def rotation_for(fig, label):
        for t in fig.axes[0].texts:
            if t.get_text() == label:
                return t.get_rotation(), t.get_va(), t.get_rotation_mode()
        return None
    rot2 = rotation_for(fig2, "Build")
    rot3 = rotation_for(fig3, "Build")
    assert rot2 and rot3
    assert rot3[0] == rot2[0] + 10
    assert rot3[1] == 'baseline' and rot3[2] == 'anchor'

def test_build_status_map_and_pdf_long_token(tmp_path):
    levels = LEVELS
    items = [
        {"Stage": "Build", "Capability": "CI", levels[0]: "A"*120, levels[1]: "", levels[2]: ""},
    ]
    responses_all = {"ProductA": {"CI": {levels[0]: "Completed"}}}
    smap = build_status_map(items, responses_all["ProductA"], levels)
    assert smap[("Build", levels[0])] == 'completed'

    # long token in description should not break PDF
    import matplotlib.pyplot as plt
    fig1, ax1 = plt.subplots(figsize=(2,2), subplot_kw=dict(polar=True))
    fig2, ax2 = plt.subplots(figsize=(2,2), subplot_kw=dict(polar=True))
    from sre_core import pdf_report
    tmp = pdf_report.generate_pdf(
        product="ProductA",
        maturity_items=items,
        responses=responses_all["ProductA"],
        fig_stage=fig1,
        fig_cap=fig2,
    )
    assert os.path.getsize(tmp.name) > 0


def test_figure_to_image_and_pdf(tmp_path):
    # simple fig
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    img, _ = figure_to_image(fig)
    assert img.size[0] > 0 and img.size[1] > 0

    # minimal PDF render with tiny figures
    items, responses_all = sample_data()
    import pandas as pd
    # build tiny stage/cap radar figs
    fig1, ax1 = plt.subplots(figsize=(2, 2), subplot_kw=dict(polar=True))
    fig2, ax2 = plt.subplots(figsize=(2, 2), subplot_kw=dict(polar=True))
    tmp = pdf_report.generate_pdf(
        product="ProductA",
        maturity_items=items,
        responses=responses_all["ProductA"],
        fig_stage=fig1,
        fig_cap=fig2,
    )
    p = tmp.name
    stat = os.stat(p)
    assert stat.st_size > 0
