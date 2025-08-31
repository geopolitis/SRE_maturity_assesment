# SRE Maturity Assessment App

This application lets organisations or teams assess, compare, and visualise the maturity of their engineering (SRE , DevOps, Security etc) practices across multiple dimensions using a structured maturity model.(BYO Model)

Demo [here](https://assessment.opsatscale.com/)

## Features

- Interactive questionnaire across 64 capabilities and 10 maturity stages(sample)
- Support for multiple products with comparison
- Automatic score calculation and visualization
- Radar charts for maturity by Stage and Capability
- Degree of Implementation ring (sunburst‑like) by Stage/Level
- Half‑donut grid for Stage completion overview
- PDF report export with diagrams and narrative sections
  - Page 1: Degree of Implementation ring
  - Page 2: Stage/Capability radars (top) + Donuts (bottom)
  - Following pages: Completed, Partially Achieved, Not Achieved sections
- Upload and manage custom capability models via CSV
- Fully persistent responses using JSON storage



## Getting Started

### Install Dependencies

```bash
pip install -r requirements.txt
````


### Run the App

```bash
streamlit run Home.py
```

### Using the App

* Go to the sidebar:

  * Add your first product
  * Upload a custom Capabilities.csv (optional)
* Complete the questionnaire
* Generate visual report (page "Visual Report")
* Download the full PDF (page "PDF Report")
  - Includes the ring, both radars, donuts and detailed sections

## Input File Format: Capabilities.csv

Must include the following headers:

```
Stage, Capability, Beginner, Intermediate, Advanced, Expert, Next-Gen (2025+)
```

Each row represents a unique maturity capability in the Good-M3 framework.

## Customization

You can edit:

* Capabilities.csv to adjust capabilities or levels
* `sre_core/constants.py` → `LEVELS` to adjust maturity levels
* Colours and styles:
  - Donuts thresholds (red/yellow/green): `sre_core/gauges.py` → `_half_donut`
  - Ring chart blue + partial alpha: `sre_core/gauges.py` → `ring_maturity_by_stage`

## Output

- PDF Report contains:
  - Title with product and timestamp
  - Page 1: Degree of Implementation (ring)
  - Page 2: Two radars (Stage/Capability) and Donuts grid
  - Narrative sections with capability‑level answers grouped by status

## Quick Run

```bash
# clone + run (one-off)
bash scripts/clone_and_run.sh /opt/assessment-app/app 8502 127.0.0.1

# or from a checked-out repo
chmod +x scripts/*.sh
./scripts/run_streamlit.sh
```

## Install as a Service

```bash
# clone + install systemd service (runs on 127.0.0.1:8502)
sudo bash scripts/clone_and_install_service.sh /opt/assessment-app/app streamlit-assessment streamlit 8502

# logs
sudo journalctl -u streamlit-assessment -f --no-pager
```

If you see venv errors, ensure the OS package for venv is installed:

```bash
sudo apt-get update && sudo apt-get install -y python3-venv
```
