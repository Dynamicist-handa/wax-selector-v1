
import streamlit as st
import pandas as pd
import pdfplumber
import re
import plotly.express as px

st.set_page_config(page_title="Physics-informed Wax Additive Selection", layout="wide")
st.markdown(
    """
    <div style='text-align: center;'>
        <a href='https://www.ecopals.de/' target='_blank'>
            <img src='https://raw.githubusercontent.com/Dynamicist-handa/wax-selector-v1/main/ecopals_logo.png' width='120'>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h1 style='text-align: center; color: #1f4f5a; white-space: nowrap;'>
        Physics-informed Wax Additive Selection: Optimize Processing!
    </h1>
    """,
    unsafe_allow_html=True
)

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
    "density": "Density23C",
    "dichte": "Density23C",
    "viscosity (140 °c)": "Viscosity135C",
    "viskosität (140 °c)": "Viscosity135C",
    "acid value": "AcidValue",
    "saurezahl": "AcidValue"
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
        return sum(matches[:2]) / len(matches[:2]) if matches else None
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
    return score

def parse_pdf(file):
    parsed = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and len(row) >= 2:
                        key, val = row[0], row[1]
                        if key and val:
                            norm_key = normalize_property(key)
                            value = try_parse_float(val)
                            if norm_key:
                                parsed[norm_key] = value
    parsed["Score"] = score_wax(parsed)
    parsed["SourceFile"] = file.name
    return parsed

results = []

uploaded_files = st.file_uploader("Upload PDF wax spec sheets", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        wax = parse_pdf(file)
        results.append(wax)

st.subheader("📝 Manual Entry")
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
    cols_to_show = ["DropMeltingPoint", "AcidValue", "Viscosity135C", "Penetration25C", "Density23C", "Score", "SourceFile"]
    df_show = df[[col for col in cols_to_show if col in df.columns]]
    st.dataframe(df_show.sort_values(by="Score", ascending=False), use_container_width=True)

    # CSV download
    csv = df_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download as CSV", data=csv, file_name="wax_scores.csv", mime="text/csv")

    # Radar plot with condition
    st.subheader("📊 Radar Plot Comparison")
    selected_waxes = st.multiselect("Select up to 3 waxes to compare:", df_show["SourceFile"].unique(), max_selections=3)

    if selected_waxes and len(selected_waxes) > 1:
        df_plot = df_show[df_show["SourceFile"].isin(selected_waxes)]
        radar_df = df_plot.set_index("SourceFile")[["DropMeltingPoint", "Viscosity135C", "Penetration25C", "Density23C", "AcidValue", "OilContent"]]
        fig = px.line_polar(
            radar_df.reset_index(),
            r=radar_df.values.flatten(),
            theta=radar_df.columns.tolist() * len(radar_df),
            line_close=True,
            color=df_plot["SourceFile"].repeat(len(radar_df.columns)).values
        )
        st.plotly_chart(fig, use_container_width=True)
    elif selected_waxes:
        st.info("Select at least 2 waxes for radar plot comparison.")
