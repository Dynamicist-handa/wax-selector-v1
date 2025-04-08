
import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

st.set_page_config(page_title="Wax Selector", layout="wide")

st.title("🧪 AI-Based Wax Selection Tool")
st.markdown("Upload **PDF** wax spec sheets to evaluate their suitability for PMB formulations. (Image support is only available in the local version)")

property_aliases = {
    "dropmeltingpoint": "DropMeltingPoint",
    "drop point": "DropMeltingPoint",
    "tropfpunkt": "DropMeltingPoint",
    "congealing point": "CongealingPoint",
    "solidification point": "CongealingPoint",
    "oil content": "OilContent",
    "oil content %": "OilContent",
    "penetration": "Penetration25C",
    "needle pen.": "Penetration25C",
    "penetration (25 °c)": "Penetration25C",
    "density": "Density23C",
    "dichte": "Density23C",
    "density (23 °c)": "Density23C",
    "viscosity (140 °c)": "Viscosity135C",
    "viskositat (140 °c)": "Viscosity135C",
    "viscosity at 135°c": "Viscosity135C",
    "acid value": "AcidValue",
    "saurezahl": "AcidValue",
    "saponification value": "SaponificationValue",
    "type": "Type"
}

def normalize_property(name):
    key = name.strip().lower()
    for alias in property_aliases:
        if alias in key:
            return property_aliases[alias]
    return key.replace(" ", "")

def try_parse_float(val):
    try:
        cleaned = re.sub(r"[^\d.,\-+]", " ", str(val))
        cleaned = cleaned.replace(",", ".")
        matches = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", cleaned)]
        if not matches:
            return None
        return sum(matches[:2]) / len(matches[:2])
    except:
        return None

def score_wax(wax):
    score = 0
    if 102 <= wax.get("DropMeltingPoint", -999) <= 115: score += 2
    if 5 <= wax.get("Penetration25C", -999) <= 9: score += 2
    if 0.91 <= wax.get("Density23C", -999) <= 0.96: score += 2
    if wax.get("Viscosity135C", 0) >= 18: score += 2
    if 100 <= wax.get("CongealingPoint", -999) <= 110: score += 1
    if wax.get("OilContent", 1) <= 0.5: score += 1
    if wax.get("AcidValue", 1) <= 0.3: score += 1
    if "fischer" in str(wax.get("Type", "")).lower(): score += 1
    return score

def parse_pdf_file(file, filename):
    text_blocks = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_blocks.extend(text.split('\n'))
    data = {}
    for line in text_blocks:
        if ':' in line:
            key, val = map(str.strip, line.split(':', 1))
        else:
            parts = re.split(r'\s{2,}', line)
            if len(parts) < 2:
                continue
            key, val = parts[0], parts[1]
        norm_key = normalize_property(key)
        value = try_parse_float(val)
        if norm_key:
            data[norm_key] = value
    data["Score"] = score_wax(data)
    data["SourceFile"] = filename
    return data

uploaded_files = st.file_uploader("Upload PDF spec sheets only", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        wax = parse_pdf_file(file, file.name)
        results.append(wax)

    df = pd.DataFrame(results)
    important_cols = ["DropMeltingPoint", "AcidValue", "Viscosity135C", "Penetration25C", "Density23C", "Score", "SourceFile"]
    df = df[[col for col in important_cols if col in df.columns]]
    st.dataframe(df.sort_values(by="Score", ascending=False), use_container_width=True)
