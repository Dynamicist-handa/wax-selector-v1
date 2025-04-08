
import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Wax Selector – Table Parser + Manual Entry Fallback", layout="wide")
st.title("🧪 Wax Selector (PDF Table Parser + Manual Entry Fallback)")

property_aliases = {
    "dropmeltingpoint": "DropMeltingPoint",
    "drop point": "DropMeltingPoint",
    "tropfpunkt": "DropMeltingPoint",
    "congealing point": "CongealingPoint",
    "solidification point": "CongealingPoint",
    "oil content": "OilContent",
    "ölgehalt": "OilContent",
    "penetration": "Penetration25C",
    "needle pen.": "Penetration25C",
    "penetration (25 °c)": "Penetration25C",
    "density": "Density23C",
    "dichte": "Density23C",
    "density (23 °c)": "Density23C",
    "viscosity (140 °c)": "Viscosity135C",
    "viskosität (140 °c)": "Viscosity135C",
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
    def safe_get(key, default=-999.0):
        try:
            return float(wax.get(key, default))
        except (ValueError, TypeError):
            return default

    score = 0
    if 102 <= safe_get("DropMeltingPoint") <= 115: score += 2
    if 5 <= safe_get("Penetration25C") <= 9: score += 2
    if 0.91 <= safe_get("Density23C") <= 0.96: score += 2
    if safe_get("Viscosity135C") >= 18: score += 2
    if 100 <= safe_get("CongealingPoint") <= 110: score += 1
    if safe_get("OilContent", 1.0) <= 0.5: score += 1
    if safe_get("AcidValue", 1.0) <= 0.3: score += 1
    if "fischer" in str(wax.get("Type", "")).lower(): score += 1
    return score

def extract_from_table(file):
    parsed = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and len(row) >= 2:
                        key = row[0]
                        val = row[1]
                        if key and val:
                            norm_key = normalize_property(key)
                            value = try_parse_float(val)
                            if norm_key:
                                parsed[norm_key] = value
    return parsed

def parse_pdf_file(file):
    filename = file.name
    parsed = extract_from_table(file)
    if len(parsed) < 2:
        file.seek(0)
        lines = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split('\n'))
        for line in lines:
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
                parsed[norm_key] = value
    parsed["Score"] = score_wax(parsed)
    parsed["SourceFile"] = filename
    return parsed

uploaded_files = st.file_uploader("Upload PDF wax spec sheets", type=["pdf"], accept_multiple_files=True)
results = []

if uploaded_files:
    for file in uploaded_files:
        wax = parse_pdf_file(file)
        results.append(wax)

st.subheader("📝 Manual Entry (if PDF parsing failed)")
with st.expander("Add wax manually"):
    col0, col1, col2, col3 = st.columns(4)
    wax_manual = {}
    wax_manual["SourceFile"] = col0.text_input("Wax Name / ID", value="Manual Entry")
    wax_manual["DropMeltingPoint"] = col1.number_input("Drop Melting Point (°C)", min_value=50.0, max_value=160.0, step=0.1)
    wax_manual["Viscosity135C"] = col2.number_input("Viscosity at 135°C (mPa·s)", min_value=0.0, step=0.1)
    wax_manual["Penetration25C"] = col3.number_input("Penetration at 25°C (dmm)", min_value=0.0, step=0.1)
    wax_manual["Density23C"] = col1.number_input("Density at 23°C (g/cm³)", min_value=0.0, step=0.001)
    wax_manual["AcidValue"] = col2.number_input("Acid Value (mg KOH/g)", min_value=0.0, step=0.1)
    wax_manual["OilContent"] = col3.number_input("Oil Content (%)", min_value=0.0, step=0.1)

    if st.button("Add Manual Entry"):
        wax_manual["Score"] = score_wax(wax_manual)
        results.append(wax_manual)

if results:
    df = pd.DataFrame(results)
    important_cols = ["DropMeltingPoint", "AcidValue", "Viscosity135C", "Penetration25C", "Density23C", "Score", "SourceFile"]
    df = df[[col for col in important_cols if col in df.columns]]
    st.dataframe(df.sort_values(by="Score", ascending=False), use_container_width=True)
