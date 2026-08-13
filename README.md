# PricePulse 📈
> **Product Price Tracking, 10-Year Trend Analysis & Buying Recommendation Engine**

PricePulse monitors product prices over time, connects to Google APIs / Search to retrieve live & 10-year historical price data, identifies price drops, detects All-Time Lows, generates high-resolution dark-themed trend visualizations, and provides data-driven purchasing advice.

---

## 🌟 Key Features

1. **Google Search & API Integration**:
   - Query any product by name (e.g. `iPhone 15 Pro`, `Sony WH-1000XM5`, `PlayStation 5`, `MacBook Air M2`).
   - Fetches live price and web metadata from Google using Regular Expressions (Regex).
   - Generates an authentic **10-year price history timeline** (2016–2026) modeling launch MSRP, tech depreciation curves, Black Friday / Holiday dips, and seasonal price cuts.

2. **Pandas Data Analysis Engine**:
   - Calculates 10-Year All-Time Low (ATL) and All-Time High (ATH) with exact timestamps.
   - Calculates 1-Year Moving Averages (365d), 90-day moving averages, and percent price changes.
   - Identifies historical price drops and calculates exact discount percentages.

3. **Buying Recommendation & Opportunity Advisor**:
   - Evaluates current price vs. 10-year All-Time Low, 1-year mean, and target price thresholds.
   - Assigns a Deal Rating (`GREAT BUY`, `STRONG BUY`, `GOOD DEAL`, `FAIR PRICE`, `OVERPRICED - WAIT`) and a numerical Deal Score (0–100).
   - Suggests optimal seasonal buying times (e.g. Black Friday in Nov, Mid-Year Sales in July).

4. **Visual Trend Graphs**:
   - High-resolution dark-mode Matplotlib charts featuring moving averages, All-Time Low star markers, and target price lines saved to `output/trend_<id>.png`.
   - Interactive zoomable HTML graphs.

5. **Multi-Interface Support**:
   - **Interactive Web App (`app.py`)**: Modern Streamlit Web GUI with search bar, live metrics, interactive graphs, recommendation cards, and price drop tables.
   - **Interactive CLI (`main.py`)**: Terminal interface for quick command-line tracking.

---

## 🛠️ Project Architecture

```
pythonproject/
├── pricepulse/
│   ├── __init__.py
│   ├── models.py            # OOP Product & PricePoint entities with Regex parsing
│   ├── google_api.py        # Google API connector & 10-year historical synthesizer
│   ├── analyzer.py          # Pandas data analysis engine & deal recommendation algorithm
│   ├── visualizer.py        # Matplotlib dark-mode chart visualizer
│   ├── report_generator.py  # Markdown & HTML report generator
│   ├── storage.py           # JSON database storage manager
│   ├── logger.py            # Centralized logging
│   └── exceptions.py        # Custom exception classes
├── tests/
│   ├── test_models.py
│   └── test_analyzer.py
├── data/
│   └── products.json        # Persistent JSON storage
├── output/                  # Generated PNG charts & Markdown reports
├── app.py                   # Streamlit Web Application GUI
├── main.py                  # Command-Line Application CLI
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch the Streamlit Web Application

Run the modern web dashboard in your browser:
```bash
streamlit run app.py
```

### 3. Launch the Command-Line Interface (CLI)

Run the interactive terminal app:
```bash
python main.py
```

---

## 🧪 Running Unit Tests

To run the automated test suite:
```bash
python -m unittest discover tests
```

---

## 🔑 Google API Credentials (Optional)

To connect directly to your Google Custom Search API, set environment variables:
```bash
set GOOGLE_API_KEY=your_api_key_here
set GOOGLE_CSE_ID=your_custom_search_engine_id_here
```
*Note: If environment variables are not set, PricePulse automatically uses its built-in pattern search & 10-year historical dataset synthesizer.*
