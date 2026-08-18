"""
SmartClass Dashboard
Run with:  streamlit run app/streamlit_app.py   (from the smartclass/ folder)
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from analysis import (load_combined, plot_heatmap, plot_scheduled_vs_actual,
                       plot_gap_by_period, plot_capacity_vs_occupancy, plot_top_bottom_rooms,
                       chi_square_block_availability, anova_occupancy_by_block,
                       correlation_capacity_occupancy, gap_by_block, underutilized_capacity)
from recommend import recommend_rooms, historical_confidence

st.set_page_config(page_title="SmartClass", layout="wide", page_icon="🏫")

st.title("🏫 SmartClass: Classroom Availability & Occupancy Analysis")
st.caption("Timetable-scheduled availability vs. actual, real-world availability.")

df = load_combined()

tab1, tab2, tab3 = st.tabs(["📊 EDA & Insights", "📈 Statistical Analysis", "🔍 Find a Room"])

# ---------------- TAB 1: EDA ----------------
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall actual availability", f"{df['actually_available'].mean():.1%}")
    col2.metric("Scheduled-free rate", f"{df['scheduled_free'].mean():.1%}")
    gap_rate = df["availability_gap"].sum() / df["scheduled_free"].sum()
    col3.metric("Availability GAP rate", f"{gap_rate:.1%}",
                help="Of the slots free on paper, this % are NOT actually usable.")

    st.subheader("Actual Availability — Block x Period Heatmap")
    st.pyplot(plot_heatmap(df))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Scheduled-Free vs Actually-Available")
        st.pyplot(plot_scheduled_vs_actual(df))
    with c2:
        st.subheader("Availability Gap Across the Day")
        st.pyplot(plot_gap_by_period(df))

    st.subheader("Most / Least Available Classrooms")
    st.pyplot(plot_top_bottom_rooms(df))

    st.subheader("Capacity vs Occupancy Ratio")
    st.pyplot(plot_capacity_vs_occupancy(df))
    st.caption("If the trend line is roughly flat, room size does not predict how crowded it gets.")

# ---------------- TAB 2: Stats ----------------
with tab2:
    st.subheader("Significance Testing")
    chi2, p_chi, dof = chi_square_block_availability(df)
    f, p_anova = anova_occupancy_by_block(df)
    r, p_corr = correlation_capacity_occupancy(df)

    st.markdown(f"""
    **Chi-square test — is actual availability independent of block?**
    χ² = {chi2:.2f}, dof = {dof}, p = {p_chi:.4f}
    → {"Block **does** significantly affect actual availability." if p_chi < 0.05 else "No significant relationship found."}

    **ANOVA — does occupancy ratio differ across blocks?**
    F = {f:.2f}, p = {p_anova:.4f}
    → {"Yes, occupancy levels differ significantly by block." if p_anova < 0.05 else "No significant difference across blocks."}

    **Pearson correlation — capacity vs occupancy ratio**
    r = {r:.3f}, p = {p_corr:.4f}
    → {"Larger rooms are meaningfully more/less crowded." if p_corr < 0.05 else "Room capacity has no meaningful relationship with how crowded it gets."}
    """)

    st.subheader("Availability Gap Rate by Block")
    st.bar_chart(gap_by_block(df))

    st.subheader("Average Occupancy by Capacity Tier")
    st.bar_chart(underutilized_capacity(df))

# ---------------- TAB 3: Recommender ----------------
with tab3:
    st.subheader("Find a genuinely available classroom")
    c1, c2, c3, c4 = st.columns(4)
    day = c1.selectbox("Day", sorted(df["day"].unique()))
    period = c2.selectbox("Period", sorted(df["period"].unique()))
    block = c3.selectbox("Your current block", sorted(df["block"].unique()))
    min_cap = c4.number_input("Min. group size", min_value=1, value=1, step=1)

    results = recommend_rooms(df, day=day, period=period, student_block=block, min_capacity=min_cap)

    if results.empty:
        st.warning("No genuinely available rooms found for this day/period near you. "
                   "Try widening your search to a different period, or check the heatmap tab "
                   "for which periods tend to be better campus-wide.")
    else:
        results["confidence (historical)"] = results["classroom_id"].apply(
            lambda cid: historical_confidence(df, cid, day, period))
        st.dataframe(
            results.rename(columns={
                "classroom_id": "Room", "block": "Block", "floor": "Floor",
                "capacity": "Capacity", "occupancy_ratio": "Current Occupancy",
                "proximity_score": "Distance (0=same block)"
            }),
            use_container_width=True, hide_index=True
        )
        st.caption("Ranked by proximity to your block, then by how quiet the room currently is.")
