# SmartClass: Data-Driven Classroom Availability & Occupancy Analysis
### Fundamentals of Data Science — Complete Project Documentation

---

## 1. Final Project Definition

SmartClass is a data science project that analyzes the gap between **timetable-scheduled classroom availability** and **actual, real-world classroom availability** on a college campus. It combines a scheduling dataset with a simulated occupancy dataset (modeled on realistic sources like Wi-Fi login logs or QR check-in systems) to compute *true* availability, identify usage patterns across time slots and blocks, and recommend genuinely free classrooms to students during free periods.

The project is not a booking/CRUD app — its deliverable is **insight**: statistical patterns in classroom usage, quantified mismatch between "timetable-free" and "actually-free," and a lightweight recommendation layer built on top of that analysis.

## 2. Problem Statement

A timetable tells a student a classroom has no scheduled class, but it says nothing about informal occupancy — students studying, group discussions, leftover crowds from the previous period, etc. As a result, students waste time walking to rooms that are technically "free" but practically unusable. There is no data-driven way to know, campus-wide, which rooms are *actually* available at a given time, nor any analysis of *when* and *where* this scheduling-vs-reality gap is worst.

## 3. Objectives

- Quantify the difference between scheduled and actual classroom availability.
- Identify time slots, blocks, and rooms with the highest/lowest genuine availability.
- Detect underutilized capacity (rooms booked/occupied far below their capacity).
- Build a rule-based recommendation engine that suggests genuinely free rooms near a student's location.
- Demonstrate the full data science pipeline: collection → cleaning → EDA → statistics → visualization → insight → recommendation.

## 4. Real-World Usefulness

- Saves student time between classes.
- Surfaces underused infrastructure to campus facilities/admin (e.g., "Block C is 40% empty during periods 5–6").
- Could inform better timetable planning (spread classes to reduce clustering in popular blocks).
- Cheap to pilot: no new hardware, works off logs institutions likely already generate (Wi-Fi/QR).

## 5. Features

**Analytics core (the actual project):**
- Cleaned, merged dataset of schedule + occupancy
- Derived "actual availability" flag per room/time slot
- EDA dashboards: heatmaps, bar charts, trend lines
- Statistical tests on availability differences across blocks/time slots
- Gap metric: `scheduled_available − actually_available`

**Applied layer (demonstrates the analytics is useful):**
- Free-period room recommender (filters by availability, capacity, block proximity)
- Simple what-if: predicted availability probability for a given room/slot (optional, secondary)

## 6. Data Fields / Dataset Structure

**`classrooms.csv`**
| Field | Type | Description |
|---|---|---|
| classroom_id | string | e.g. A101 |
| block | string | A / B / C |
| floor | int | 1–3 |
| capacity | int | seats |

**`timetable.csv`**
| Field | Type | Description |
|---|---|---|
| classroom_id | string | FK to classrooms |
| day | string | Mon–Fri |
| period | int | 1–8 |
| start_time / end_time | time | period bounds |
| subject | string | scheduled class, or "FREE" |
| scheduled | bool | True if a class is officially scheduled |

**`occupancy_log.csv`** (simulated, modeled on Wi-Fi/QR check-in logs)
| Field | Type | Description |
|---|---|---|
| classroom_id | string | FK |
| date | date | specific date instance |
| day | string | Mon–Fri |
| period | int | 1–8 |
| students_present | int | informal headcount (self-reported/passive log derived) |
| source | string | "wifi_log" / "qr_checkin" (simulated tag) |

**Derived `combined_dataset.csv`** (built by the cleaning pipeline):
`classroom_id, block, capacity, day, period, scheduled, subject, students_present, occupancy_ratio, actually_available, availability_gap`

## 7. Data Collection Methodology

For the prototype, real logs aren't accessible, so data is **simulated with realistic statistical structure** rather than pure random noise:
- Peak periods (mid-morning, post-lunch) get higher occupancy probability.
- Popular blocks (near cafeteria/library) get higher informal occupancy.
- Occupancy is capped and shaped by room capacity (small rooms fill up faster).
- Scheduled classes follow a realistic weekly timetable structure (no two classes in one room at the same time).

This mirrors how such data would be collected in production: Wi-Fi access-point association logs or QR check-in scans at the door, aggregated to headcounts per room per period — **no facial recognition, no cameras, no new IoT.**

## 8. Data Cleaning & Preprocessing

- Handle missing occupancy readings (impute as 0 or drop, documented explicitly).
- Standardize classroom IDs, block names, time formats.
- Remove duplicate log entries (same room/date/period logged twice).
- Detect and cap outlier headcounts (students_present > capacity → flag/cap).
- Merge `classrooms` + `timetable` + `occupancy_log` on `classroom_id`/`day`/`period`.
- Derive:
  - `occupancy_ratio = students_present / capacity`
  - `actually_available = (scheduled == False) AND (occupancy_ratio < 0.2)`
  - `availability_gap = scheduled_free_but_not_actually_available` (boolean flag for mismatch)

## 9. EDA Questions

1. Which classrooms are most frequently available (scheduled-free vs actually-free)?
2. Which classrooms are most frequently occupied (by class or by informal use)?
3. Which time slots have highest actual availability campus-wide?
4. Which blocks have most unused classroom space?
5. What's the average gap between scheduled and actual availability, per block/time slot?
6. Which periods are hardest for students to find a room?
7. Which capacity tier (small/medium/large rooms) is most underutilized?
8. Is there a day-of-week effect (e.g., Fridays quieter)?
9. Correlation between room capacity and likelihood of informal occupation.

## 10. Recommended Graphs & Visualizations

- Heatmap: rooms × periods, colored by actual availability (the signature chart)
- Grouped bar chart: scheduled-free % vs actually-free % per block
- Line chart: availability trend across periods 1–8, per day
- Box plot: occupancy ratio distribution by capacity tier
- Bar chart: top 10 most/least available rooms
- Stacked bar: reasons a room is unavailable (class scheduled vs informally occupied)
- Scatter plot: capacity vs average occupancy ratio (underutilization check)

## 11. Statistical Analysis

- Descriptive stats: mean/median occupancy ratio per block, per period
- Chi-square test: is "actual availability" independent of block? Of time slot?
- T-test / ANOVA: do occupancy ratios differ significantly across blocks?
- Correlation: capacity vs occupancy ratio (Pearson)
- Gap rate: % of scheduled-free slots that are NOT actually available (the headline statistic)

## 12. Recommendation Logic

Rule-based, not ML, because the rules are simple and interpretable — this is the right tool for the job:

```
def recommend_rooms(day, period, student_block, min_capacity=1, top_n=5):
    1. Filter combined_dataset for day == day, period == period
    2. Keep rows where actually_available == True
    3. Filter capacity >= min_capacity
    4. Rank by:
       a. Same block as student (priority 1)
       b. Lower occupancy_ratio (quieter room, priority 2)
       c. Capacity closest to student's group size (priority 3)
    5. Return top_n classroom_ids with block, capacity, occupancy_ratio
```
Optional secondary layer: a simple historical-frequency "confidence score" — how often has this room been actually available at this day/period historically — surfaced as a probability, not a black-box prediction.

## 13. System Workflow

```
[Raw schedule + simulated occupancy logs]
        ↓
[Cleaning & merging pipeline] → combined_dataset.csv
        ↓
[EDA + statistical analysis] → charts, insights, gap metrics
        ↓
[Recommendation engine] → filters combined_dataset for a query
        ↓
[Streamlit dashboard] → visual EDA tab + "Find me a room" tab
```

## 14. Technology Stack

- **Python 3** — core language
- **Pandas / NumPy** — cleaning, merging, aggregation
- **Matplotlib / Seaborn** — statistical visualizations
- **SciPy** — significance testing (chi-square, t-test)
- **Streamlit** — interactive dashboard (EDA + recommender UI)
- **CSV** as the dataset store (sufficient for project scale; SQLite optional upgrade)

## 15. Project Architecture

```
smartclass/
├── data/
│   ├── classrooms.csv
│   ├── timetable.csv
│   ├── occupancy_log.csv
│   └── combined_dataset.csv        (generated)
├── generate_data.py                (simulated data generator)
├── pipeline.py                     (cleaning + merging + derived fields)
├── analysis.py                     (EDA + stats, saves figures)
├── recommend.py                    (recommendation logic, importable)
├── app/
│   └── streamlit_app.py            (dashboard)
└── PROJECT_DOCUMENTATION.md
```

## 16. Database / Dataset Design

CSV files are sufficient at this scale (30 rooms × 5 days × 8 periods ≈ 1,200 timetable rows, similar occupancy rows). Relationships:
`classrooms (1) —— (many) timetable`
`classrooms (1) —— (many) occupancy_log`
join key: `classroom_id` (+ `day`, `period` for timetable/occupancy alignment).
An SQLite version is a listed future enhancement, not required for the core deliverable.

## 17. Sample Dataset

See generated files in `data/` — realistic, not perfectly random: peak periods and popular blocks show measurably higher occupancy, which is what makes the EDA meaningful.

## 18. Expected Outputs

- Cleaned combined dataset (CSV)
- 6–8 visualizations with written insights
- Statistical test results with interpretation (not just p-values — plain-English conclusions)
- A working "find me a room" recommender in the dashboard
- A one-page summary of key findings (e.g., "Block B periods 4–5 have only 18% actual availability despite 55% scheduled availability")

## 19. Edge Cases

- No rooms available at all in a block/period → recommend nearest other block, say so explicitly.
- All rooms at 0% occupancy (holiday/exam gap) → don't over-recommend, just show all.
- Room with 0 capacity data (data entry error) → exclude with a logged warning.
- Occupancy exceeding capacity (over-crowded/logging error) → cap ratio at 1.0, flag for review.
- Student's own block has nothing available → widen search radius (adjacent blocks) automatically.

## 20. Testing Strategy

- Unit tests on `pipeline.py` functions (merge correctness, derived field logic) using small hand-built mock CSVs with known expected output.
- Sanity checks: `occupancy_ratio` always in [0, 1] after cleaning; no duplicate (classroom_id, day, period) rows.
- Manual verification: spot-check 5–10 recommendation outputs against the raw combined dataset.

## 21. Future Enhancements

- Real integration with institutional Wi-Fi/QR logs (replace simulator)
- SQLite/Postgres backend for larger scale
- Lightweight predictive model (logistic regression) for "probability room X is free next period," trained on historical patterns — clearly labeled as a secondary, optional feature
- Mobile-friendly UI
- Campus map with real block-adjacency graph for genuine distance ranking

## 22. FDS Concepts Demonstrated

Data collection design, data cleaning (missing values, duplicates, outliers), merging/joining relational data, feature engineering (derived ratios/flags), descriptive statistics, inferential statistics (chi-square, t-test, correlation), exploratory data analysis, data visualization best practices, pattern identification, insight generation, and translating analysis into an actionable recommendation system.

## 23. Possible Viva Questions & Answers

**Q: Why not just use a booking system?**
A: A booking system assumes compliance; this project's core value is exposing where *actual* behavior diverges from the schedule — that divergence is the data science question, not room allocation itself.

**Q: Why rule-based recommendation instead of ML?**
A: The decision logic (available + capacity + proximity) is fully known and interpretable; ML would add opacity without improving accuracy. ML is reserved for the one place it adds value — historical probability estimation — and even that is optional.

**Q: How would you validate the simulated data reflects reality?**
A: By designing generation probabilities from plausible real patterns (peak-hour clustering, block popularity) and, in a real deployment, calibrating against a short manual audit (walking around and counting) before trusting Wi-Fi/QR logs fully.

**Q: What's your single most important statistic?**
A: The "availability gap rate" — the percentage of timetable-free slots that are NOT actually usable. That number is the entire justification for the project.

**Q: What was the hardest data cleaning decision?**
A: Deciding the occupancy threshold for "actually available" (e.g., <20% capacity) — an arbitrary-seeming cutoff that needs justification via distribution analysis (see occupancy ratio histogram), not just picked out of thin air.

**Q: What are the limitations?**
A: Simulated (not real) occupancy data; block-proximity distance is a rough proxy, not true path distance; recommendation logic doesn't account for noise level, temperature, or non-quantified comfort factors.
