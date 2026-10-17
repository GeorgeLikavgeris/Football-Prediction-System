import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from scipy.stats import poisson

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "all_leagues_2026.csv"
OUTPUT_FILE = BASE_DIR / "data" / "predictions_all.csv"
ENV_PATH = BASE_DIR / "info.env"

load_dotenv(ENV_PATH)

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError(f"Missing API_KEY in {ENV_PATH}")

HEADERS = {"X-Auth-Token": API_KEY}
BASE_URL = "https://api.football-data.org/v4"
SEASON = 2026
LAST_N_MATCHES = 5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

LEAGUE_CODES = {
    "Premier League": "PL",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "La Liga": "PD",
    "Eredivisie": "DED",
    "Primeira Liga": "PPL",
    "Championship": "ELC",
    "Ligue 1": "FL1",
}

TEAM_NAME_MAP = {
    "1. FC Heidenheim 1846": "FC Heidenheim 1846",
    "1. FC Köln": "FC Köln",
    "1. FC Union Berlin": "FC Union Berlin",
    "1. FSV Mainz 05": "FSV Mainz 05",
}


def fix_team_name(name):
    return TEAM_NAME_MAP.get(name, name)


# --------------------------------------------------
# LOAD AND PREPARE HISTORICAL DATA
# --------------------------------------------------
def load_matches():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required = [
        "date", "league", "home_team", "away_team",
        "home_score_ft", "away_score_ft",
        "home_score_ht", "away_score_ht", "matchday",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")

    score_columns = [
        "home_score_ft", "away_score_ft",
        "home_score_ht", "away_score_ht",
    ]

    for col in score_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["date", "league", "home_team", "away_team"] + score_columns
    ).copy()

    # Keep completed matches only.
    # The collection script already filters for FINISHED matches.
    df["home_team"] = df["home_team"].map(fix_team_name)
    df["away_team"] = df["away_team"].map(fix_team_name)

    df = df.sort_values("date").reset_index(drop=True)

    logging.info("Loaded %s completed matches", len(df))
    return df


# --------------------------------------------------
# FIND THE NEXT MATCHDAY
# --------------------------------------------------
def get_next_fixtures(league, historical_matches):
    code = LEAGUE_CODES[league]

    league_history = historical_matches[
        historical_matches["league"] == league
    ]

    if league_history.empty:
        logging.warning("No historical matches found for %s", league)
        return pd.DataFrame()

    matchdays = pd.to_numeric(
        league_history["matchday"], errors="coerce"
    ).dropna()

    if matchdays.empty:
        logging.warning("No matchday information for %s", league)
        return pd.DataFrame()

    next_matchday = int(matchdays.max()) + 1

    try:
        response = requests.get(
            f"{BASE_URL}/competitions/{code}/matches",
            headers=HEADERS,
            params={
                "season": SEASON,
                "matchday": next_matchday,
            },
            timeout=15,
        )

        response.raise_for_status()
        matches = response.json().get("matches", [])

    except requests.RequestException as exc:
        logging.error("Fixture request failed for %s: %s", league, exc)
        return pd.DataFrame()

    fixtures = []

    for match in matches:
        # Predict upcoming matches only.
        if match.get("status") not in {"SCHEDULED", "TIMED"}:
            continue

        home_team = match.get("homeTeam", {}).get("name")
        away_team = match.get("awayTeam", {}).get("name")

        if not home_team or not away_team:
            continue

        fixtures.append({
            "date": pd.to_datetime(
                match.get("utcDate"), utc=True, errors="coerce"
            ),
            "matchday": match.get("matchday"),
            "home_team": fix_team_name(home_team),
            "away_team": fix_team_name(away_team),
        })

    return pd.DataFrame(fixtures)


# --------------------------------------------------
# LAST 5 MATCHES FOR EACH TEAM
# Home and away matches are both included.
# Only matches before the fixture date are considered.
# --------------------------------------------------
def get_recent_team_stats(history, team, fixture_date):
    before_fixture = history[history["date"] < fixture_date]

    team_matches = before_fixture[
        (before_fixture["home_team"] == team)
        | (before_fixture["away_team"] == team)
    ].sort_values("date", ascending=False).head(LAST_N_MATCHES)

    if len(team_matches) < LAST_N_MATCHES:
        return None

    is_home = team_matches["home_team"].eq(team)

    scored_ft = np.where(
        is_home,
        team_matches["home_score_ft"],
        team_matches["away_score_ft"],
    )

    conceded_ft = np.where(
        is_home,
        team_matches["away_score_ft"],
        team_matches["home_score_ft"],
    )

    scored_ht = np.where(
        is_home,
        team_matches["home_score_ht"],
        team_matches["away_score_ht"],
    )

    conceded_ht = np.where(
        is_home,
        team_matches["away_score_ht"],
        team_matches["home_score_ht"],
    )

    return {
        "matches_used": len(team_matches),
        "avg_scored_ft": float(np.mean(scored_ft)),
        "avg_conceded_ft": float(np.mean(conceded_ft)),
        "avg_scored_ht": float(np.mean(scored_ht)),
        "avg_conceded_ht": float(np.mean(conceded_ht)),
    }


# --------------------------------------------------
# EXPECTED GOALS
# Recent team performance is normalized against
# league-wide goal averages.
# --------------------------------------------------
def expected_goals(home, away, league_averages):
    league_team_ft = league_averages["team_ft"]
    league_team_ht = league_averages["team_ht"]

    # Full-time expected goals
    exp_home_ft = (
        league_averages["home_ft"]
        * home["avg_scored_ft"] / league_team_ft
        * away["avg_conceded_ft"] / league_team_ft
    )

    exp_away_ft = (
        league_averages["away_ft"]
        * away["avg_scored_ft"] / league_team_ft
        * home["avg_conceded_ft"] / league_team_ft
    )

    # Half-time expected goals
    if league_team_ht > 0:
        exp_home_ht = (
            league_averages["home_ht"]
            * home["avg_scored_ht"] / league_team_ht
            * away["avg_conceded_ht"] / league_team_ht
        )

        exp_away_ht = (
            league_averages["away_ht"]
            * away["avg_scored_ht"] / league_team_ht
            * home["avg_conceded_ht"] / league_team_ht
        )
    else:
        exp_home_ht = 0.0
        exp_away_ht = 0.0

    # Protect against invalid values.
    expected = [
        exp_home_ft, exp_away_ft, exp_home_ht, exp_away_ht,
    ]

    expected = [max(0.0, float(x)) for x in expected]

    return expected


def get_league_averages(history):
    return {
        "home_ft": history["home_score_ft"].mean(),
        "away_ft": history["away_score_ft"].mean(),
        "team_ft": (
            history["home_score_ft"].mean()
            + history["away_score_ft"].mean()
        ) / 2,
        "home_ht": history["home_score_ht"].mean(),
        "away_ht": history["away_score_ht"].mean(),
        "team_ht": (
            history["home_score_ht"].mean()
            + history["away_score_ht"].mean()
        ) / 2,
    }


# --------------------------------------------------
# POISSON SCORE MATRIX
# --------------------------------------------------
def poisson_matrix(exp_home, exp_away, max_goals=10):
    home_goals = np.arange(max_goals + 1)
    away_goals = np.arange(max_goals + 1)

    home_probs = poisson.pmf(home_goals, exp_home)
    away_probs = poisson.pmf(away_goals, exp_away)

    matrix = np.outer(home_probs, away_probs)

    # Normalize probabilities in the truncated score matrix.
    total = matrix.sum()
    if total > 0:
        matrix = matrix / total

    return matrix


def calculate_probabilities(matrix, over_line):
    home_win = np.tril(matrix, -1).sum()
    draw = np.diag(matrix).sum()
    away_win = np.triu(matrix, 1).sum()

    # For over 2.5, under means total goals <= 2.
    # For over 0.5, under means total goals == 0.
    over = sum(
        matrix[i, j]
        for i in range(matrix.shape[0])
        for j in range(matrix.shape[1])
        if i + j > over_line
    )

    return home_win, draw, away_win, over


# --------------------------------------------------
# MAIN PREDICTION PIPELINE
# --------------------------------------------------
def run_predictions():
    historical = load_matches()
    results = []

    for league in LEAGUE_CODES:
        logging.info("Processing %s", league)

        league_history = historical[
            historical["league"] == league
        ].copy()

        if league_history.empty:
            logging.warning("No data for %s", league)
            continue

        fixtures = get_next_fixtures(league, league_history)

        if fixtures.empty:
            logging.info("No upcoming fixtures found for %s", league)
            continue

        for _, fixture in fixtures.iterrows():
            home_team = fixture["home_team"]
            away_team = fixture["away_team"]
            fixture_date = fixture["date"]

            if pd.isna(fixture_date):
                logging.warning("Invalid fixture date; skipping match")
                continue

            home_stats = get_recent_team_stats(
                league_history, home_team, fixture_date
            )
            away_stats = get_recent_team_stats(
                league_history, away_team, fixture_date
            )

            if home_stats is None or away_stats is None:
                logging.warning(
                    "Fewer than %s prior matches: %s vs %s",
                    LAST_N_MATCHES, home_team, away_team,
                )
                continue

            # Use only league matches played before this fixture.
            history_before_fixture = league_history[
                league_history["date"] < fixture_date
            ]

            if history_before_fixture.empty:
                continue

            averages = get_league_averages(history_before_fixture)

            if averages["team_ft"] <= 0:
                logging.warning("Invalid league averages for %s", league)
                continue

            (
                exp_home_ft, exp_away_ft,
                exp_home_ht, exp_away_ht,
            ) = expected_goals(home_stats, away_stats, averages)

            matrix_ft = poisson_matrix(exp_home_ft, exp_away_ft)
            matrix_ht = poisson_matrix(exp_home_ht, exp_away_ht)

            home, draw, away, over25 = calculate_probabilities(
                matrix_ft, over_line=2
            )

            home_ht, draw_ht, away_ht, over05 = calculate_probabilities(
                matrix_ht, over_line=0
            )

            results.append({
                "league": league,
                "home_team": home_team,
                "away_team": away_team,

                # Full-time predictions
                "ft_exp_home": round(exp_home_ft, 2),
                "ft_exp_away": round(exp_away_ft, 2),
                "ft_home_win": round(home * 100, 2),
                "ft_draw": round(draw * 100, 2),
                "ft_away_win": round(away * 100, 2),
                "ft_over_2_5": round(over25 * 100, 2),
                "ft_under_2_5": round((1 - over25) * 100, 2),

                # Half-time predictions
                "ht_exp_home": round(exp_home_ht, 2),
                "ht_exp_away": round(exp_away_ht, 2),
                "ht_home_win": round(home_ht * 100, 2),
                "ht_draw": round(draw_ht * 100, 2),
                "ht_away_win": round(away_ht * 100, 2),
                "ht_over_0_5": round(over05 * 100, 2),
                "ht_under_0_5": round((1 - over05) * 100, 2),

                # Audit information
                "home_last5_matches": home_stats["matches_used"],
                "away_last5_matches": away_stats["matches_used"],
                "fixture_date": fixture_date,
                "matchday": fixture.get("matchday"),
            })

    return pd.DataFrame(results)


# --------------------------------------------------
# RUN AND SAVE
# --------------------------------------------------
if __name__ == "__main__":
    predictions = run_predictions()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(OUTPUT_FILE, index=False)

    print("\nPredictions generated:")
    if predictions.empty:
        print("No predictions were generated.")
    else:
        print(predictions.head().to_string(index=False))

    print(f"\nTotal predictions: {len(predictions)}")
    print(f"Saved to: {OUTPUT_FILE}")
