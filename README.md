# SRE Maturity Assessment App

This Streamlit application allows organisations to assess, compare, and visualise the maturity of their SRE practices across multiple products using the SRE maturity model.

## Features

- Interactive questionnaire across 64 capabilities and 10 maturity stages
- Support for multiple products with comparison
- Automatic score calculation and visualization
- Radar charts for maturity by Stage and Capability
- PDF report export including scores, charts, and timestamps
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

### 3. Using the App

* Go to the sidebar:

  * Add your first product
  * Upload a custom Capabilities.csv (optional)
* Complete the questionnaire
* Generate report
* Download the full PDF including radar charts

## Input File Format: Capabilities.csv

Must include the following headers:

```
Stage, Capability, Beginner, Intermediate, Advanced, Expert, Next-Gen (2025+)
```

Each row represents a unique maturity capability in the Good-M3 framework.

## Customization

You can edit:

* Capabilities.csv to adjust capabilities or levels
* LEVELS and LEVEL\_SCORES in main.py for scoring adjustments

## Output

* PDF Report with:

  * Capability-level answers
  * Timestamp
  * Product name
  * Radar charts for:

    * Maturity by Stage
    * Maturity by Capability

