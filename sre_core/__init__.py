"""
sre_core package
Core utilities for the SRE Maturity Assessment Streamlit app.

This package contains:
- constants.py     → Global constants and scoring definitions
- data_io.py       → CSV load/validation utilities
- persistence.py   → Save/load of user responses
- scoring.py       → Convert responses to DataFrame with scores
- formatting.py    → Text/Markdown report formatting
- plotting.py      → Radar chart helpers
- pdf_report.py    → PDF generation with charts and sections
- widgets.py       → Streamlit form widgets for assessment
"""

from .constants import LEVELS, SUB_LEVELS, SUB_LEVEL_SCORES
from .data_io import load_capabilities, dataframe_to_items
from .persistence import load_responses, save_responses
from .scoring import build_df
from .formatting import markdown_report
from .plotting import plot_radar
from .pdf_report import generate_pdf
from .widgets import assessment_ui

__all__ = [
    "LEVELS",
    "SUB_LEVELS",
    "SUB_LEVEL_SCORES",
    "load_capabilities",
    "dataframe_to_items",
    "load_responses",
    "save_responses",
    "build_df",
    "markdown_report",
    "plot_radar",
    "generate_pdf",
    "assessment_ui",
]
