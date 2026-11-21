# 📊 Analytics AutoPilot

> Turn raw data into an executive-ready PowerPoint report in seconds — no manual charting, no slide design, no copy-pasting.

---

## 🚀 What It Does

Upload any sales/business CSV or Excel file and Analytics AutoPilot will automatically:

1. **Detect** your columns (date, revenue, profit, category, region)
2. **Compute** all key KPIs (Revenue, Profit, Margin, MoM Growth, Best Month, etc.)
3. **Generate** 4 publication-quality interactive charts
4. **Write** executive insights and talking points
5. **Build** a fully branded 5-slide PowerPoint deck — ready to present

---

## 📁 Project Structure

```
analytics-autopilot/
│
├── app.py               # Streamlit web interface (main entry point for users)
├── run_pipeline.py      # CLI runner — runs the full pipeline end-to-end
│
├── generate_data.py     # Generates realistic sample retail sales data
├── analysis_engine.py   # Computes all KPIs, trends, rankings
├── chart_engine.py      # Generates 4 Plotly charts and exports as PNG
├── slide_builder.py     # Assembles the PowerPoint deck (python-pptx)
│
├── output/              # Generated charts (.png) and deck (.pptx) — git ignored
├── requirements.txt     # Python dependencies
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/analytics-autopilot.git
cd analytics-autopilot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the web app
```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

### 4. Or run the CLI pipeline
```bash
python run_pipeline.py
```

---

## 📦 Requirements

- Python 3.9+
- pandas
- plotly
- kaleido (for PNG chart export)
- python-pptx
- streamlit
- openpyxl

---

## 🗺️ Roadmap

- [ ] v0.1 — Core pipeline + Streamlit web UI ✅
- [ ] v0.2 — Custom branding (logo upload, color picker)
- [ ] v0.3 — AI-powered narrative generation (Gemini API integration)
- [ ] v0.4 — PDF export option
- [ ] v0.5 — Multi-sheet Excel support
- [ ] v1.0 — SaaS deployment with user accounts and Stripe billing

---

## 💡 Motivation

Built to eliminate the most painful part of data analytics work: spending hours in PowerPoint arranging charts and formatting slides instead of actually interpreting data.

---

## 📄 License

MIT License — free to use, modify, and build on.
