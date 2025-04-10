
import streamlit as st
import pandas as pd
import base64
import io
import pdfplumber
import plotly.express as px

st.set_page_config(page_title="Physics-informed Wax Additive Selection: Optimize Processing!", layout="wide")

st.markdown(
    '''
    <div style='text-align: center; padding-bottom: 10px;'>
        <a href='https://www.ecopals.de/' target='_blank'>
            <img src='https://raw.githubusercontent.com/Dynamicist-handa/wax-selector-v1/main/ecopals_logo.png' width='120'>
        </a>
        <h1 style='color:#004d5c;'>Physics-informed Wax Additive Selection: Optimize Processing!</h1>
    </div>
    ''', unsafe_allow_html=True
)

st.subheader("Upload PDF wax spec sheets")
uploaded_files = st.file_uploader("Drag and drop files here", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

with st.expander("📝 Manual Entry"):
    manual_name = st.text_input("Wax Name / ID", "Manual Entry")
    manual_drop_point = st.number_input("Drop Melting Point (°C)", value=50.0)
    manual_viscosity = st.number_input("Viscosity at 135°C (mPa·s)", value=0.0)
    manual_penetration = st.number_input("Penetration at 25°C (dmm)", value=0.0)
    manual_density = st.number_input("Density at 23°C (g/cm³)", value=0.0)
    manual_acid = st.number_input("Acid Value (mg KOH/g)", value=0.0)
    manual_oil = st.number_input("Oil Content (%)", value=0.0)

    if st.button("Add Manual Entry"):
        st.session_state.setdefault("wax_data", [])
        st.session_state.wax_data.append({
            "DropMeltingPoint": manual_drop_point,
            "Viscosity135C": manual_viscosity,
            "Penetration25C": manual_penetration,
            "Density23C": manual_density,
            "AcidValue": manual_acid,
            "OilContent": manual_oil,
            "Score": 0,
            "SourceFile": manual_name
        })

def normalize_property(name):
    aliases = {
        "drop point": "DropMeltingPoint", "tropfpunkt": "DropMeltingPoint",
        "congealing point": "DropMeltingPoint", "solidification": "DropMeltingPoint",
        "viscosity": "Viscosity135C",
        "penetration": "Penetration25C",
        "density": "Density23C",
        "acid value": "AcidValue", "saurezahl": "AcidValue",
        "oil content": "OilContent"
    }
    name = name.lower().strip()
    for key in aliases:
        if key in name:
            return aliases[key]
    return name.replace(" ", "")

def extract_table_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
    return pd.DataFrame()

def parse_pdf(file, filename):
    df_raw = extract_table_from_pdf(file)
    parsed = {"SourceFile": filename}
    if not df_raw.empty:
        for _, row in df_raw.iterrows():
            if len(row) >= 2:
                key, val = row[0], row[1]
                key = normalize_property(str(key))
                try:
                    val = float(str(val).replace(",", ".").split()[0])
                except:
                    continue
                parsed[key] = val
    return parsed

parsed_data = []
if "wax_data" in st.session_state:
    parsed_data.extend(st.session_state.wax_data)

if uploaded_files:
    for file in uploaded_files:
        wax = parse_pdf(file, file.name)
        parsed_data.append(wax)

if parsed_data:
    df = pd.DataFrame(parsed_data)
    display_cols = ["DropMeltingPoint", "Viscosity135C", "Penetration25C", "Density23C", "AcidValue", "OilContent", "Score", "SourceFile"]
    for col in display_cols:
        if col not in df.columns:
            df[col] = None
    df_show = df[display_cols]
    st.dataframe(df_show, use_container_width=True)

    csv = df_show.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download as CSV", csv, "wax_data.csv", "text/csv")

    st.markdown("### 📊 Radar Plot Comparison")
    selected = st.multiselect("Select up to 3 waxes to compare:", df_show["SourceFile"].unique(), max_selections=3)
    if selected:
        radar_df = df_show[df_show["SourceFile"].isin(selected)]
        radar_df = radar_df.set_index("SourceFile")
        radar_df = radar_df[["DropMeltingPoint", "Viscosity135C", "Penetration25C", "Density23C", "AcidValue", "OilContent"]]
        if not radar_df.isnull().values.any():
            fig = px.line_polar(radar_df.reset_index(), r=radar_df.values.flatten(), theta=radar_df.columns,
                                line_close=True, color=radar_df.reset_index()["SourceFile"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Radar plot not available: some required properties are missing.")
