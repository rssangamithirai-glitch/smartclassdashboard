"""
SmartClass — Rule-based classroom recommendation engine.
Deliberately NOT ML: the decision logic is fully known, so a transparent
rule-based ranking is the right (and more trustworthy) tool.
"""
import pandas as pd

# rough block-adjacency proxy (used instead of true geodesic distance)
BLOCK_ADJACENCY = {
    "A": {"A": 0, "B": 1, "C": 2},
    "B": {"A": 1, "B": 0, "C": 1},
    "C": {"A": 2, "B": 1, "C": 0},
}


def recommend_rooms(df: pd.DataFrame, day: str, period: int, student_block: str,
                     min_capacity: int = 1, top_n: int = 5) -> pd.DataFrame:
    """Return top_n genuinely available rooms for a given day/period/location."""
    subset = df[(df["day"] == day) & (df["period"] == period)].copy()
    subset = subset[subset["actually_available"] & (subset["capacity"] >= min_capacity)]

    if subset.empty:
        return subset  # caller should handle "no rooms found"

    subset["proximity_score"] = subset["block"].map(lambda b: BLOCK_ADJACENCY[student_block][b])
    subset = subset.sort_values(by=["proximity_score", "occupancy_ratio"], ascending=[True, True])

    return subset[["classroom_id", "block", "floor", "capacity", "occupancy_ratio",
                    "proximity_score"]].head(top_n).reset_index(drop=True)


def historical_confidence(df: pd.DataFrame, classroom_id: str, day: str, period: int) -> float:
    """Optional secondary signal: how often has this room been actually
    available at this day/period historically? Simple frequency, not a
    black-box model -- kept transparent on purpose."""
    subset = df[(df["classroom_id"] == classroom_id) & (df["day"] == day) & (df["period"] == period)]
    if subset.empty:
        return float("nan")
    return subset["actually_available"].mean()


if __name__ == "__main__":
    combined = pd.read_csv("data/combined_dataset.csv")
    result = recommend_rooms(combined, day="Mon", period=4, student_block="B", top_n=5)
    print(result)
