import streamlit as st
import pandas as pd

# --------------------------------
# PAGE CONFIG
# --------------------------------

st.set_page_config(layout="wide")
st.title("⚽ Football Predictions Dashboard")

# --------------------------------
# LOAD DATA
# --------------------------------

@st.cache_data
def load_data():
    return pd.read_csv("data/predictions_all.csv")

df = load_data()

# --------------------------------
# LEAGUE FILTER
# --------------------------------

league = st.selectbox(
    "Select League",
    sorted(df["league"].unique())
)

league_df = df[df["league"] == league].copy()
league_df["match"] = league_df["home_team"] + " vs " + league_df["away_team"]

# --------------------------------
# MATCH FILTER
# --------------------------------

match = st.selectbox(
    "Select Match",
    league_df["match"]
)

match_data = league_df[league_df["match"] == match].iloc[0]

home = match_data["home_team"]
away = match_data["away_team"]

st.header(f"{home} vs {away}")

# --------------------------------
# TABS
# --------------------------------

tab1, tab2, tab3 = st.tabs([
    "📊 Overview",
    "⚽ Full Time",
    "⏱ Half Time"
])

# =================================
# TAB 1 - OVERVIEW
# =================================

with tab1:

    st.subheader("Expected Goals")

    col1, col2 = st.columns(2)
    col1.metric(home, match_data["ft_exp_home"])
    col2.metric(away, match_data["ft_exp_away"])

    st.markdown("---")

    st.subheader("Match Probabilities")

    col1, col2, col3 = st.columns(3)
    col1.metric("Home Win", f"{match_data['ft_home_win']}%")
    col2.metric("Draw", f"{match_data['ft_draw']}%")
    col3.metric("Away Win", f"{match_data['ft_away_win']}%")

    st.markdown("---")

    col1, col2 = st.columns(2)
    col1.metric("Over 2.5", f"{match_data['ft_over_2_5']}%")
    col2.metric("Under 2.5", f"{match_data['ft_under_2_5']}%")

# =================================
# TAB 2 - FULL TIME
# =================================

with tab2:

    st.subheader("Full Time Probabilities")

    col1, col2, col3 = st.columns(3)
    col1.metric(home, f"{match_data['ft_home_win']}%")
    col2.metric("Draw", f"{match_data['ft_draw']}%")
    col3.metric(away, f"{match_data['ft_away_win']}%")

    st.markdown("---")

    st.subheader("Over / Under 2.5")

    col1, col2 = st.columns(2)
    col1.metric("Over 2.5", f"{match_data['ft_over_2_5']}%")
    col2.metric("Under 2.5", f"{match_data['ft_under_2_5']}%")

    st.markdown("---")

    st.subheader("Expected Goals")

    col1, col2 = st.columns(2)
    col1.metric(home, match_data["ft_exp_home"])
    col2.metric(away, match_data["ft_exp_away"])

# =================================
# TAB 3 - HALF TIME
# =================================

with tab3:

    st.subheader("Half Time Probabilities")

    col1, col2, col3 = st.columns(3)
    col1.metric(home, f"{match_data['ht_home_win']}%")
    col2.metric("Draw", f"{match_data['ht_draw']}%")
    col3.metric(away, f"{match_data['ht_away_win']}%")

    st.markdown("---")

    st.subheader("Over / Under 0.5 (HT)")

    col1, col2 = st.columns(2)
    col1.metric("Over 0.5", f"{match_data['ht_over_0_5']}%")
    col2.metric("Under 0.5", f"{match_data['ht_under_0_5']}%")

    st.markdown("---")

    st.subheader("Expected Goals (HT)")

    col1, col2 = st.columns(2)
    col1.metric(home, match_data["ht_exp_home"])
    col2.metric(away, match_data["ht_exp_away"])

# =================================
# FULL TABLE
# =================================

st.markdown("---")
st.subheader("All Matches (League View)")

st.dataframe(
    league_df.drop(columns=["match"]),
    use_container_width=True
)