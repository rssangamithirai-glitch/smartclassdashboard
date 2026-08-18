"""
SmartClass — Cleaning & Preprocessing Pipeline
Merges classrooms + timetable + occupancy_log, cleans, and derives the
fields the whole analysis depends on: occupancy_ratio, actually_available,
availability_gap.
"""
import pandas as pd
import numpy as np

DATA_DIR = "data"
AVAILABILITY_THRESHOLD = 0.20  # occupancy_ratio below this = "actually available"


def load_raw():
    classrooms = pd.read_csv(f"{DATA_DIR}/classrooms.csv")
    timetable = pd.read_csv(f"{DATA_DIR}/timetable.csv")
    occupancy = pd.read_csv(f"{DATA_DIR}/occupancy_log.csv")
    return classrooms, timetable, occupancy


def clean_timetable(timetable):
    before = len(timetable)
    timetable = timetable.drop_duplicates(subset=["classroom_id", "day", "period"])
    removed = before - len(timetable)
    print(f"[clean_timetable] removed {removed} duplicate rows")
    timetable["scheduled"] = timetable["scheduled"].astype(bool)
    return timetable


def clean_occupancy(occupancy, classrooms):
    before = len(occupancy)
    occupancy = occupancy.drop_duplicates(subset=["classroom_id", "date", "day", "period"])
    print(f"[clean_occupancy] removed {before - len(occupancy)} duplicate rows")

    missing = occupancy["students_present"].isna().sum()
    occupancy["students_present"] = occupancy["students_present"].fillna(0)
    print(f"[clean_occupancy] imputed {missing} missing values with 0")

    # cap students_present at capacity (fix over-crowded logging errors)
    occupancy = occupancy.merge(classrooms[["classroom_id", "capacity"]], on="classroom_id", how="left")
    over = (occupancy["students_present"] > occupancy["capacity"]).sum()
    occupancy["students_present"] = occupancy[["students_present", "capacity"]].min(axis=1)
    print(f"[clean_occupancy] capped {over} over-capacity readings")
    occupancy = occupancy.drop(columns=["capacity"])
    return occupancy


def build_combined(classrooms, timetable, occupancy):
    df = timetable.merge(classrooms, on="classroom_id", how="left")
    df = df.merge(
        occupancy[["classroom_id", "day", "period", "students_present", "source"]],
        on=["classroom_id", "day", "period"], how="left"
    )
    df["students_present"] = df["students_present"].fillna(0)
    df["occupancy_ratio"] = (df["students_present"] / df["capacity"]).round(3)
    df["occupancy_ratio"] = df["occupancy_ratio"].clip(upper=1.0)

    df["actually_available"] = (~df["scheduled"]) & (df["occupancy_ratio"] < AVAILABILITY_THRESHOLD)
    df["scheduled_free"] = ~df["scheduled"]
    df["availability_gap"] = df["scheduled_free"] & (~df["actually_available"])

    cols = ["classroom_id", "block", "floor", "capacity", "day", "period",
            "start_time", "end_time", "subject", "scheduled", "students_present",
            "occupancy_ratio", "scheduled_free", "actually_available", "availability_gap", "source"]
    return df[cols]


if __name__ == "__main__":
    classrooms, timetable, occupancy = load_raw()
    timetable = clean_timetable(timetable)
    occupancy = clean_occupancy(occupancy, classrooms)
    combined = build_combined(classrooms, timetable, occupancy)
    combined.to_csv(f"{DATA_DIR}/combined_dataset.csv", index=False)

    print(f"\ncombined_dataset.csv -> {len(combined)} rows")
    print(f"Overall actual availability rate: {combined['actually_available'].mean():.1%}")
    print(f"Overall scheduled-free rate:      {combined['scheduled_free'].mean():.1%}")
    print(f"Availability GAP rate (free-on-paper but not really): "
          f"{combined['availability_gap'].sum() / combined['scheduled_free'].sum():.1%}")
