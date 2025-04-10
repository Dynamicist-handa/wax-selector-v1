
import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Wax Additive Selector", layout="wide")

st.title("Physics-informed Wax Additive Selection")

# Alias mapping for property recognition
property_aliases = {
    "drop point": "DropMeltingPoint",
    "tropfpunkt": "DropMeltingPoint",
    "congealing point": "DropMeltingPoint",
    "viscosity": "Viscosity135C",
    "penetration": "Penetration25C",
    "density": "Density23C",
    "acid value": "AcidValue",
    "saurezahl": "AcidValue",
    "oil content": "OilContent"
}

def normalize_property(name):
    key = name.lower().strip()
    for alias in property_aliases:
        if alias in key:
            return property_aliases[alias]
    return key.replace(" ", "")

def try_parse_float(val):
    try:
        cleaned = re.sub(r"[^\d.,\-+]", " ", str(val)).replace(",", ".")
        matches = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", cleaned)]
        return sum(matches[:2]) / len(matches[:2]) if matches else None
    except:
        return None

def parse_pdf_file(file):
    parsed = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table:
                    if row and len(row) >= 2:
                        key, val = row[0], row[1]
                        norm_key = normalize_property(str(key))
                        value = try_parse_float(val)
                        if norm_key:
                            parsed[norm_key] = value
    parsed["SourceFile"] = file.name
    return parsed

def wax_environmental_insight(wax):
    hints = []
    oil = wax.get("OilContent", None)
    acid = wax.get("AcidValue", None)
    source = wax.get("SourceFile", "this wax")

    if oil is not None:
        if oil <= 0.5:
            hints.append("🔹 Low oil content – environmentally inert")
        elif oil > 1:
            hints.append("⚠️ High oil content – may pose environmental persistence risk")

    if acid is not None:
        if acid <= 0.3:
            hints.append("🔹 Low acid value – minimal oxidative degradation")
        elif acid > 1:
            hints.append("⚠️ High acid value – risk of reactivity or instability")

    if not hints:
        return f"Not enough chemical indicators were found to assess the environmental footprint of {source}."
    return "\n".join(hints)

uploaded_files = st.file_uploader("Upload wax PDF spec sheets", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        parsed = parse_pdf_file(file)
        results.append(parsed)

    df = pd.DataFrame(results)
    st.dataframe(df)

    st.subheader("🔬 Sustainability Insights")
    for wax in results:
        st.markdown(f"**{wax['SourceFile']}**")
        st.code(wax_environmental_insight(wax), language="markdown")
