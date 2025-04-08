# 🧪 Wax Selector AI Tool

This is an AI-assisted material selection tool for ranking wax additives used in polymer-modified bitumen (PmB) formulations. It helps R&D and formulation teams evaluate wax candidates based on their physicochemical properties extracted from specification sheets (PDFs or images).

---

## 🎯 Purpose

Designed by Rishab Handa at EcoPals GmbH, this tool streamlines the screening of wax additives based on:

- Viscosity impact
- Compatibility with PE/PP/SBS-modified bitumen
- Crystallization behavior
- Thermo-rheological properties

---

## 🚀 Features

- 🧠 Intelligent scoring of waxes using property-based benchmarks
- 📎 Upload wax spec sheets as PDF or image (JPG/PNG)
- 🔍 Auto-extraction via OCR or PDF parsing
- 📊 Sorted ranking with scientific weighting system
- 🧪 Designed to guide real-world material testing and formulation

---

## 🛠️ How to Use (Locally)

Install requirements:
```bash
pip install -r requirements.txt
```

Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

---

## 📂 Files

| File                | Description                                  |
|---------------------|----------------------------------------------|
| `streamlit_app.py`  | Main app script                              |
| `requirements.txt`  | Python dependencies                          |
| `README.md`         | This file                                    |

---

## 🌍 Deployment on Streamlit Cloud

1. Fork or clone this repo
2. Push to your own GitHub account
3. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
4. Click “New App” and select this repo
5. Choose `streamlit_app.py` and deploy!

---

## 📚 Scientific Context

This tool supports the EcoPals R&D initiative to optimize recycled plastic and wax-enhanced binders for asphalt and road infrastructure. Scoring criteria are based on:

- Standard PMB testing thresholds
- Bitumen-wax-polymer compatibility literature
- Viscosity & crystallization benchmarks for optimal wet mixing

---

## 👨‍🔬 Author

**Dr. Rishab Handa**  
Principal R&D Scientist
(Advanced Material Computation)  
EcoPals GmbH