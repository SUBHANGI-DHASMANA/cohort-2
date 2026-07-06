# Cohort 2 — Analytics Dashboard

Short, self-contained analytics dashboard and data-processing project containing scripts, a small web dashboard, and example datasets.

## Project Overview

- Interactive dashboard (HTML/JS/CSS) and lightweight Python app for generating and exploring sales and inventory analytics.
- Includes data generation and pipeline scripts, example CSV datasets, and a Jupyter notebook for experimentation.

## Contents

- `app.py` — Entry point for the web dashboard / application.
- `dashboard.html`, `dashboard.js`, `dashboard.css` — Frontend dashboard assets.
- `analytics_pipeline.py` — Data processing pipeline used to transform and aggregate transactions.
- `data_generator.py` — Utility to create synthetic example data.
- `accelerated_analytics.ipynb` — Notebook with exploratory analysis and visualizations.
- `transactions.csv`, `stores.csv`, `inventory.csv` — Example datasets.
- `requirements.txt` — Python dependencies.

## Requirements

- Python 3.9+ recommended
- Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

1. (Optional) Generate or refresh example data:

```bash
python data_generator.py
```

2. Run data pipeline to produce aggregated outputs:

```bash
python analytics_pipeline.py
```

3. Start the app / dashboard (if `app.py` exposes a web server):

```bash
python app.py
# then open the URL printed by the script (commonly http://localhost:5000)
```

4. Or open `accelerated_analytics.ipynb` with Jupyter Lab / Notebook for exploration.

## Docker

Build and run via the included `Dockerfile` (if present):

```bash
docker build -t cohort-2-dashboard .
docker run -p 5000:5000 cohort-2-dashboard
```

## Data

Example CSV files are included in the repository. These are safe to inspect and use to exercise the dashboard.

## Development

- Edit frontend assets in `dashboard.*` and backend logic in `app.py` / `analytics_pipeline.py`.
- Run the notebook for exploratory analysis and to prototype new visualizations.

## License & Attribution

This repository is provided as-is for learning and demonstration. Add a license file if you intend to publish or share broadly.

---

If you'd like a shorter README, a more detailed setup, or specific run instructions for `app.py`, tell me which behavior you prefer and I will revise.
