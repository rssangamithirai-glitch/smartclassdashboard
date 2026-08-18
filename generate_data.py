"""
SmartClass — Simulated Data Generator
Generates classrooms.csv, timetable.csv, occupancy_log.csv with REALISTIC
statistical structure (not pure randomness): peak-hour clustering, block
popularity, and capacity-based crowding, so the downstream EDA has real
patterns to discover.
"""
import numpy as np
import pandas as pd
import random

np.random.seed(42)
random.seed(42)

OUT_DIR = "data"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS = list(range(1, 9))  # 8 periods/day
PERIOD_TIMES = {
    1: ("08:00", "08:50"), 2: ("08:50", "09:40"), 3: ("09:50", "10:40"),
    4: ("10:40", "11:30"), 5: ("11:30", "12:20"), 6: ("13:10", "14:00"),
    7: ("14:00", "14:50"), 8: ("14:50", "15:40"),
}
# relative "busyness" of each period (informal occupancy tendency) -- peaks
# mid-morning (free-period lounging) and right after lunch
PERIOD_BUSYNESS = {1: 0.15, 2: 0.20, 3: 0.35, 4: 0.45, 5: 0.30,
                   6: 0.55, 7: 0.40, 8: 0.20}

BLOCKS = {
    "A": {"popularity": 0.55, "rooms": 12, "floors": 3},  # near cafeteria/library
    "B": {"popularity": 0.35, "rooms": 10, "floors": 2},
    "C": {"popularity": 0.20, "rooms": 8,  "floors": 2},  # far, less popular
}

SUBJECTS = ["Data Structures", "Probability & Stats", "DBMS", "Operating Systems",
            "Linear Algebra", "Machine Learning", "Computer Networks",
            "Software Engineering", "Economics", "Communication Skills"]


def make_classrooms():
    rows = []
    for block, cfg in BLOCKS.items():
        for i in range(1, cfg["rooms"] + 1):
            floor = ((i - 1) % cfg["floors"]) + 1
            capacity = int(np.random.choice([30, 40, 50, 60, 80], p=[0.25, 0.3, 0.25, 0.15, 0.05]))
            room_id = f"{block}{floor}{i:02d}"
            rows.append({"classroom_id": room_id, "block": block, "floor": floor, "capacity": capacity})
    return pd.DataFrame(rows)


def make_timetable(classrooms):
    rows = []
    for _, room in classrooms.iterrows():
        # each room has a randomized weekly "load factor" -- some rooms are heavily
        # timetabled, some rarely used for formal classes
        load_factor = np.random.beta(2, 2)
        for day in DAYS:
            for period in PERIODS:
                scheduled = np.random.rand() < load_factor
                subject = random.choice(SUBJECTS) if scheduled else "FREE"
                start, end = PERIOD_TIMES[period]
                rows.append({
                    "classroom_id": room["classroom_id"], "day": day, "period": period,
                    "start_time": start, "end_time": end,
                    "subject": subject, "scheduled": scheduled
                })
    df = pd.DataFrame(rows)
    # inject a few messy rows for the cleaning step to catch
    dup_sample = df.sample(5, random_state=1)
    df = pd.concat([df, dup_sample], ignore_index=True)
    return df


def make_occupancy(classrooms, timetable):
    rows = []
    merged = timetable.merge(classrooms, on="classroom_id")
    for _, r in merged.iterrows():
        block_pop = BLOCKS[r["block"]]["popularity"]
        busyness = PERIOD_BUSYNESS[r["period"]]

        if r["scheduled"]:
            # scheduled classes: occupancy roughly matches enrollment (60-95% of capacity)
            present = int(r["capacity"] * np.random.uniform(0.6, 0.95))
        else:
            # informal occupancy: driven by block popularity + period busyness
            prob_occupied = 0.15 + 0.5 * block_pop + 0.4 * busyness
            if np.random.rand() < prob_occupied:
                present = int(r["capacity"] * np.random.uniform(0.05, 0.45))
            else:
                present = int(np.random.choice([0, 0, 0, 1, 2]))  # mostly empty, occasional stray students

        # small chance of a logging glitch (missing value) for cleaning practice
        if np.random.rand() < 0.02:
            present = np.nan

        rows.append({
            "classroom_id": r["classroom_id"], "date": f"2026-08-{(hash(r['day']) % 20)+1:02d}",
            "day": r["day"], "period": r["period"],
            "students_present": present,
            "source": np.random.choice(["wifi_log", "qr_checkin"], p=[0.7, 0.3])
        })
    df = pd.DataFrame(rows)
    # inject a few duplicate log entries
    dup_sample = df.sample(8, random_state=2)
    df = pd.concat([df, dup_sample], ignore_index=True)
    return df


if __name__ == "__main__":
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    classrooms = make_classrooms()
    timetable = make_timetable(classrooms)
    occupancy = make_occupancy(classrooms, timetable)

    classrooms.to_csv(f"{OUT_DIR}/classrooms.csv", index=False)
    timetable.to_csv(f"{OUT_DIR}/timetable.csv", index=False)
    occupancy.to_csv(f"{OUT_DIR}/occupancy_log.csv", index=False)

    print("Generated:")
    print(f"  classrooms.csv   -> {len(classrooms)} rows")
    print(f"  timetable.csv    -> {len(timetable)} rows")
    print(f"  occupancy_log.csv-> {len(occupancy)} rows")
