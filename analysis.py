"""
SmartClass — EDA + Statistical Analysis
Generates the core charts and runs significance tests. Can be run standalone
(saves PNGs) or imported by the Streamlit app.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")


def load_combined(path="data/combined_dataset.csv"):
    return pd.read_csv(path)


# ---------- EDA aggregates ----------

def availability_by_room(df):
    return (df.groupby("classroom_id")["actually_available"].mean()
              .sort_values(ascending=False).rename("actual_availability_rate"))


def availability_by_block_period(df):
    return df.pivot_table(index="block", columns="period", values="actually_available", aggfunc="mean")


def gap_by_block(df):
    free = df[df["scheduled_free"]]
    return free.groupby("block")["availability_gap"].mean().rename("gap_rate")


def gap_by_period(df):
    free = df[df["scheduled_free"]]
    return free.groupby("period")["availability_gap"].mean().rename("gap_rate")


def underutilized_capacity(df):
    df = df.copy()
    df["capacity_tier"] = pd.cut(df["capacity"], bins=[0, 35, 55, 100],
                                  labels=["Small (<=35)", "Medium (36-55)", "Large (56+)"])
    return df.groupby("capacity_tier")["occupancy_ratio"].mean().rename("avg_occupancy_ratio")


# ---------- Statistical tests ----------

def chi_square_block_availability(df):
    table = pd.crosstab(df["block"], df["actually_available"])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    return chi2, p, dof


def anova_occupancy_by_block(df):
    groups = [g["occupancy_ratio"].values for _, g in df.groupby("block")]
    f, p = stats.f_oneway(*groups)
    return f, p


def correlation_capacity_occupancy(df):
    r, p = stats.pearsonr(df["capacity"], df["occupancy_ratio"])
    return r, p


# ---------- Plots ----------

def plot_heatmap(df, save_path=None):
    pivot = availability_by_block_period(df)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn", ax=ax, cbar_kws={"label": "Actual availability"})
    ax.set_title("Actual Availability Rate — Block x Period")
    ax.set_xlabel("Period")
    ax.set_ylabel("Block")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_scheduled_vs_actual(df, save_path=None):
    scheduled_free = df.groupby("block")["scheduled_free"].mean()
    actual = df.groupby("block")["actually_available"].mean()
    comp = pd.DataFrame({"Scheduled-free": scheduled_free, "Actually-available": actual})
    fig, ax = plt.subplots(figsize=(6, 4))
    comp.plot(kind="bar", ax=ax, color=["#8ecae6", "#219653"])
    ax.set_ylabel("Rate")
    ax.set_title("Scheduled-Free vs Actually-Available, by Block")
    ax.set_xticklabels(comp.index, rotation=0)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_gap_by_period(df, save_path=None):
    gp = gap_by_period(df)
    fig, ax = plt.subplots(figsize=(7, 4))
    gp.plot(kind="line", marker="o", ax=ax, color="#c0392b")
    ax.set_ylabel("Gap rate (scheduled-free but not actually available)")
    ax.set_xlabel("Period")
    ax.set_title("Availability Gap Across the Day")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_capacity_vs_occupancy(df, save_path=None):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.regplot(data=df, x="capacity", y="occupancy_ratio", scatter_kws={"alpha": 0.2}, ax=ax, color="#2c6e91")
    ax.set_title("Capacity vs Occupancy Ratio")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_top_bottom_rooms(df, save_path=None):
    rates = availability_by_room(df)
    top = rates.head(8)
    bottom = rates.tail(8)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    top.plot(kind="barh", ax=axes[0], color="#219653")
    axes[0].set_title("Most Available Rooms")
    axes[0].invert_yaxis()
    bottom.plot(kind="barh", ax=axes[1], color="#c0392b")
    axes[1].set_title("Least Available Rooms")
    axes[1].invert_yaxis()
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    df = load_combined()

    plot_heatmap(df, "outputs/heatmap.png")
    plot_scheduled_vs_actual(df, "outputs/scheduled_vs_actual.png")
    plot_gap_by_period(df, "outputs/gap_by_period.png")
    plot_capacity_vs_occupancy(df, "outputs/capacity_vs_occupancy.png")
    plot_top_bottom_rooms(df, "outputs/top_bottom_rooms.png")

    chi2, p, dof = chi_square_block_availability(df)
    f, p_anova = anova_occupancy_by_block(df)
    r, p_corr = correlation_capacity_occupancy(df)

    print("\n--- Statistical Tests ---")
    print(f"Chi-square (block vs actual availability): chi2={chi2:.2f}, p={p:.4f}, dof={dof}")
    print(f"ANOVA (occupancy ratio across blocks):      F={f:.2f}, p={p_anova:.4f}")
    print(f"Pearson correlation (capacity vs occupancy): r={r:.3f}, p={p_corr:.4f}")

    print("\n--- Gap rate by block ---")
    print(gap_by_block(df))
    print("\n--- Underutilization by capacity tier ---")
    print(underutilized_capacity(df))
    print("\nSaved 5 charts to outputs/")
