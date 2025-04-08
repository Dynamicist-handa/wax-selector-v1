import pandas as pd
import re

# Required for PDF and OCR
import pdfplumber
from PIL import Image
import pytesseract

# ------------------------
# Normalization Dictionary
# ------------------------
property_aliases = {
      "Drop melting point": "DropMeltingPoint",
    "Drop point": "DropMeltingPoint",
    "Tropfpunkt": "DropMeltingPoint",
    "Congealing point": "CongealingPoint",
    "Solidification point": "CongealingPoint",
    "Oil content": "OilContent",
    "Oil content %": "OilContent",
    "Penetration": "Penetration25C",
    "Needle pen.": "Penetration25C",
    "Penetration (25 °C)": "Penetration25C",
    "Viscosity": "Viscosity135C",
    "Viscosity (140 °C)": "Viscosity135C",
    "Viskositat (140 °C)": "Viscosity135C",
    "Viscosity at 135°C": "Viscosity135C",
    "Dichte (23 °C)": "Density23C",
    "Density (23 °C)": "Density23C",
    "Acid value": "AcidValue",
    "Saurezahl": "AcidValue",
    "Saponification value": "SaponificationValue",
    "Type": "Type"
}


# ------------------------
# Data Ingestion Functions
# ------------------------

def extract_table_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        tables = []
        for page in pdf.pages:
            for table in page.extract_tables():
                df = pd.DataFrame(table[1:], columns=table[0])
                tables.append(df)
        return pd.concat(tables, ignore_index=True) if tables else None

def extract_text_from_image(img_path):
    img = Image.open(img_path)
    raw_text = pytesseract.image_to_string(img)

    rows = [line.strip() for line in raw_text.split('\n') if line.strip()]
    data = {}

    for row in rows:
        if ':' in row:
            key, val = map(str.strip, row.split(':', 1))
        else:
            # Handle case: separated by spaces
            parts = re.split(r'\s{2,}', row)  # split by 2+ spaces
            if len(parts) < 2:
                continue
            key, val = parts[0], parts[1]
        key = normalize_property(key)
        val = try_parse_float(val)
        if key:  # only add if key is valid
            data[key] = val

    return pd.DataFrame([data])



# ------------------------
# Utilities
# ------------------------

def normalize_property(name):
    name = name.lower()
    name = name.replace("°C", "").replace("(25°C)", "25c").replace("(140°C)", "135C")
    name = name.replace("g/cm?", "g/cm³").replace("mm*107", "mm")  # Clean OCR noise
    for alias, standard in property_aliases.items():
        if alias.lower() in name:
            return standard
    return name.strip().replace(" ", "")



def try_parse_float(val):
    try:
        cleaned = re.sub(r"[^\d.,\-+]", " ", str(val))
        cleaned = cleaned.replace(",", ".")
        matches = [float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", cleaned)]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        # If two numbers (min–max), take the average
        return sum(matches[:2]) / 2
    except:
        return None




def score_wax(wax):
    score = 0
    if 102 <= wax.get("DropMeltingPoint", -999) <= 115:
        score += 2
        print("✔ DropMeltingPoint matched")
    if 5 <= wax.get("Penetration25C", -999) <= 9:
        score += 2
        print("✔ Penetration25C matched")
    if 0.91 <= wax.get("Density23C", -999) <= 0.96:
        score += 2
        print("✔ Density23C matched")
    if wax.get("Viscosity135C", 0) >= 18:
        score += 2
        print("✔ Viscosity135C matched")
    if 100 <= wax.get("CongealingPoint", -999) <= 110:
        score += 1
        print("✔ CongealingPoint matched")
    if wax.get("OilContent", 1) <= 0.5:
        score += 1
        print("✔ OilContent matched")
    if wax.get("AcidValue", 1) <= 0.3:
        score += 1
        print("✔ AcidValue matched")
    if "Fischer" in str(wax.get("Type", "")):
        score += 1
        print("✔ Type matched")
    return score


# ------------------------
# Main Workflow
# ------------------------

def evaluate_waxes(filepaths):
    all_waxes = []

    for path in filepaths:
        if path.endswith(".pdf"):
            df = extract_table_from_pdf(path)
        elif path.lower().endswith((".png", ".jpg", ".jpeg")):
            df = extract_text_from_image(path)
        else:
            df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)

        if df is not None:
            df.columns = [normalize_property(col) for col in df.columns]
            wax = df.iloc[0].to_dict()
            print(f"Extracted wax fields from {path}:\n{wax}\n")  # << Add this
            wax["Score"] = score_wax(wax)
            wax["SourceFile"] = path
            all_waxes.append(wax)
            print(f"Parsed from {path}:", wax)
            for wax in all_waxes:
                print("Parsed keys for scoring:", list(wax.keys()))

    df = pd.DataFrame(all_waxes)
    if df.empty or "Score" not in df.columns:
        print("⚠️ No valid or scorable wax data found.")
        return pd.DataFrame()
    return df.sort_values(by="Score", ascending=False)




# Example Usage
files = ["Deurex_T_39_Wax.png", "Deurex_T_19_Wax.png", "Holler_FT_Wax.png"]
ranked = evaluate_waxes(files)
print(ranked)
