# SRE Maturity App with full persistence and comparison

import streamlit as st
import uuid
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
from tempfile import NamedTemporaryFile
from PIL import Image

DATA_FILE = "responses.json"

st.sidebar.markdown("### Upload Maturity Matrix")
uploaded_file = st.sidebar.file_uploader("Upload Capabilities File", type="csv")
@st.cache_data
def load_maturity_data():
    df = pd.read_csv("Capabilities.csv")
    return [
        {
            "Stage": row["Stage"],
            "Capability": row["Capability"],
            "Beginner": row["Beginner"],
            "Intermediate": row["Intermediate"],
            "Advanced": row["Advanced"],
            "Expert": row["Expert"],
            "Next-Gen (2025+)": row["Next-Gen (2025+)"]
        }
        for _, row in df.iterrows()
    ]

if uploaded_file:
    df_uploaded = pd.read_csv(uploaded_file)
    maturity_data = [
        {
            "Stage": row["Stage"],
            "Capability": row["Capability"],
            "Beginner": row["Beginner"],
            "Intermediate": row["Intermediate"],
            "Advanced": row["Advanced"],
            "Expert": row["Expert"],
            "Next-Gen (2025+)": row["Next-Gen (2025+)"]
        }
        for _, row in df_uploaded.iterrows()
    ]
else:
    try:
        maturity_data = load_maturity_data()
    except FileNotFoundError:
        st.error("Default Capabilities.csv not found. Please upload the maturity matrix using the sidebar.")
        st.stop()

LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert", "Next-Gen (2025+)"]
LEVEL_SCORES = {level: i+1 for i, level in enumerate(LEVELS)}

def load_responses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_responses(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

if 'responses_all' not in st.session_state:
    st.session_state.responses_all = load_responses()

# Sidebar: product management
st.sidebar.header("Product Management")
new_product = st.sidebar.text_input("Add new product")
if new_product and new_product not in st.session_state.responses_all:
    st.session_state.responses_all[new_product] = {}
    save_responses(st.session_state.responses_all)
    st.rerun()

product_list = list(st.session_state.responses_all.keys()) or ["<Add a product to begin>"]
selected_product = st.sidebar.selectbox("Select a product", product_list)
if selected_product == "<Add a product to begin>":
    st.stop()

if st.sidebar.button("Delete selected product") and selected_product:
    st.session_state.responses_all.pop(selected_product, None)
    save_responses(st.session_state.responses_all)
    st.rerun()

rename = st.sidebar.text_input("Rename selected product")
if rename and rename != selected_product and rename not in st.session_state.responses_all:
    st.session_state.responses_all[rename] = st.session_state.responses_all.pop(selected_product)
    save_responses(st.session_state.responses_all)
    st.rerun()

# Questionnaire
st.title("SRE Maturity Assessment")
st.subheader(f"Assessment for: {selected_product}")
if selected_product not in st.session_state.responses_all:
    st.session_state.responses_all[selected_product] = {}
st.session_state.responses = st.session_state.responses_all[selected_product]

for i, item in enumerate(maturity_data):
    st.markdown(f"### {item['Stage']} → {item['Capability']}")
    with st.expander("Level descriptions"):
        for level in LEVELS:
            st.markdown(f"**{level}:** {item[level]}")
    default = st.session_state.responses.get(item['Capability'], LEVELS[0])
    selection = st.radio("Select your level:", LEVELS, index=LEVELS.index(default), key=f"{selected_product}_{item['Stage']}_{item['Capability']}_{i}".replace(" ", "_").replace("/", "_"))
    st.session_state.responses[item['Capability']] = selection
    save_responses(st.session_state.responses_all)

# Generate results
if st.button("Generate Report"):
    frames = []
    for prod, answers in st.session_state.responses_all.items():
        for item in maturity_data:
            level = answers.get(item['Capability'], LEVELS[0])
            frames.append({
                "Product": prod,
                "Stage": item['Stage'],
                "Capability": item['Capability'],
                "Level": level,
                "Score": LEVEL_SCORES[level]
            })
    df = pd.DataFrame(frames)
    st.dataframe(df)

    # Radar: stage level
    radar_stage = df.groupby(["Product", "Stage"])["Score"].mean().reset_index()
    labels = sorted(radar_stage['Stage'].unique().tolist())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for prod in radar_stage['Product'].unique():
        values = radar_stage[radar_stage['Product'] == prod].set_index("Stage").reindex(labels)["Score"].fillna(0).tolist()
        values += values[:1]
        ax.plot(angles, values, label=prod)
        ax.fill(angles, values, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticks(range(1, 6))
    ax.set_yticklabels(["1", "2", "3", "4", "5"])
    ax.set_title("Maturity by Stage")
    ax.legend(loc="upper right")
    st.pyplot(fig)

    # Radar: capability level
    radar_cap = df.groupby(["Product", "Capability"])["Score"].mean().reset_index()
    labels_cap = sorted(radar_cap['Capability'].unique().tolist())
    angles_cap = np.linspace(0, 2 * np.pi, len(labels_cap), endpoint=False).tolist()
    angles_cap += angles_cap[:1]

    fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for prod in radar_cap['Product'].unique():
        values = radar_cap[radar_cap['Product'] == prod].set_index("Capability").reindex(labels_cap)["Score"].fillna(0).tolist()
        values += values[:1]
        ax2.plot(angles_cap, values, label=prod)
        ax2.fill(angles_cap, values, alpha=0.1)
    ax2.set_xticks(angles_cap[:-1])
    ax2.set_xticklabels(labels_cap, fontsize=8)
    ax2.set_yticks(range(1, 6))
    ax2.set_yticklabels(["1", "2", "3", "4", "5"])
    ax2.set_title("Maturity by Capability")
    ax2.legend(loc="upper right")
    st.pyplot(fig2)

    # Save radar charts to images and generate PDF
    radar_buf = BytesIO()
    fig.savefig(radar_buf, format="png")
    radar_buf.seek(0)
    radar_img = Image.open(radar_buf)
    radar_img_path = "radar_stage.png"
    radar_img.save(radar_img_path)

    radar_cap_buf = BytesIO()
    fig2.savefig(radar_cap_buf, format="png")
    radar_cap_buf.seek(0)
    radar_cap_img = Image.open(radar_cap_buf)
    radar_cap_path = "radar_capability.png"
    radar_cap_img.save(radar_cap_path)

    pdf = FPDF()
    pdf.set_font("Arial", size=12)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.add_page()
    pdf.cell(200, 10, txt=f"SRE Maturity Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Generated: {timestamp}", ln=True, align='C')
    pdf.ln(5)

    for prod in st.session_state.responses_all:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Product: {prod}", ln=True)
        pdf.set_font("Arial", size=11)
        for item in df[df['Product'] == prod].itertuples():
            line = f"{item.Stage} | {item.Capability}: {item.Level}"
            pdf.multi_cell(0, 10, line)
        pdf.ln(4)

    pdf.add_page()
    pdf.image(radar_img_path, x=10, w=180)
    pdf.ln(5)
    pdf.image(radar_cap_path, x=10, w=180)

    with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        tmp_pdf.seek(0)
        pdf_bytes = tmp_pdf.read()

    st.sidebar.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name=f"{selected_product}_maturity_report.pdf",
        mime="application/pdf"
    )
