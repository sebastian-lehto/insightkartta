# InsightKartta

InsightKartta is a data-driven analytics application focused on exploring regional statistics in Finland. It leverages official APIs from Statistics Finland to build a full data pipeline, perform analysis, and present interactive visualizations through a modern web application.

The goal of this project is to go beyond simple data visualization by implementing a structured data pipeline, reusable analysis framework, and an interactive geospatial interface that enables meaningful insights.

---

## 🚀 Features

* 📊 **Automated Data Pipeline**

  * Ingestion from Statistics Finland PXWeb APIs
  * Generic transformation layer for PXWeb datasets
  * Dataset-specific cleaning and normalization
  * Enrichment using external mapping tables (e.g. regions)

* 🧠 **Analysis Framework**

  * Modular and extensible analysis engine
  * Insight generation (not just raw charts)
  * Designed to support multiple datasets and metrics

* 🌍 **Interactive Map Visualization**

  * Regional unemployment data displayed on a map of Finland
  * Time slider to explore changes over years
  * Dynamic coloring based on values
  * Hover tooltips with contextual information

* ⚙️ **Fullstack Architecture**

  * FastAPI backend serving processed data and analysis
  * React frontend with interactive charts and maps
  * Clean separation between data, logic, and presentation

---

## 🏗️ Project Structure

```
insightkartta/
│
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── services/         # Business logic (analysis, data access)
│   │   └── main.py           # FastAPI entrypoint
│
│   └── data/                 # Data files
│
│   ├── pipelines/
│   │   ├── ingestion/            # API data fetching
│   │   ├── transformation/       # Data transformation pipeline
│   │   └── analysis/             # Analysis framework
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components (MapView, charts)
│   │   ├── assets/           # Static assets
│   │   └── App.jsx
│   │
│   └── public/
│       └── maakunnat.geojson # Finland regions geometry
│
└── README.md
```

---

## 🔄 Data Pipeline

1. **Ingestion**

   * Fetch raw data from PXWeb APIs

2. **Transformation**

   * Convert PXWeb format → tabular DataFrame
   * Normalize column names (e.g. `Alue → region`, `Vuosi → year`)

3. **Enrichment**

   * Map region codes → region names using `region_mapping.csv`
   * Filter unsupported regions

4. **Analysis**

   * Compute insights using reusable analysis modules

---

## 🗺️ Map Integration

* Uses GeoJSON for Finnish regions (`maakunnat.geojson`)
* Matches data to regions via `region_name`
* Handles:

  * Missing mappings
  * String normalization
  * Dynamic styling

---

## 🧪 Example Insight

* Regional unemployment trends over time
* Identification of high-unemployment regions
* Temporal changes visualized via slider

---

## ⚙️ Running the Project

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Design Principles

* Separation of concerns (ingestion, transformation, analysis, presentation)
* Extensibility for new datasets and APIs
* Data validation and explicit mapping
* Reproducible pipeline

---

## 🚧 Future Improvements

* Add more datasets (income, education, population)
* Improve region mapping automation
* Add legend and UI controls to map
* Advanced analytics (correlations, forecasting)
* Data validation layer (schema checks, quality reports)

---

## 🎯 Purpose

This project is designed to demonstrate:

* Data engineering skills (ETL pipelines)
* Backend development (FastAPI)
* Frontend development (React + visualization)
* System design and architecture thinking

---
