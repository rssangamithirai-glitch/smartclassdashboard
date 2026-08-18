# SmartClass — Setup & Run Guide

## 1. Install dependencies
```bash
pip install pandas numpy matplotlib seaborn scipy streamlit
```

## 2. Generate the simulated dataset
```bash
python generate_data.py
```
Creates `data/classrooms.csv`, `data/timetable.csv`, `data/occupancy_log.csv`.

## 3. Run the cleaning/merging pipeline
```bash
python pipeline.py
```
Creates `data/combined_dataset.csv` — this is the single source of truth for everything downstream.
Prints the headline numbers (overall availability, gap rate).

## 4. Run standalone EDA + stats (optional, saves PNGs)
```bash
python analysis.py
```
Saves charts to `outputs/` and prints statistical test results.

## 5. Launch the dashboard
```bash
streamlit run app/streamlit_app.py
```
Three tabs: EDA & Insights, Statistical Analysis, Find a Room (recommender).

## Project files
- `generate_data.py` — realistic simulated data generator
- `pipeline.py` — cleaning, merging, derived fields (occupancy_ratio, actually_available, availability_gap)
- `analysis.py` — EDA aggregates, plots, statistical tests
- `recommend.py` — rule-based recommendation engine (importable + CLI test)
- `app/streamlit_app.py` — the dashboard
- `PROJECT_DOCUMENTATION.md` — full write-up (all 23 sections) for your report/viva

## For your report
Re-run `pipeline.py` and note the printed **availability gap rate** — that single
number ("X% of timetable-free slots are not actually usable") is your project's
central finding and should anchor your introduction/abstract.
