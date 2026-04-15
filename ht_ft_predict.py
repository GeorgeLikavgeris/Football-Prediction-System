import pandas as pd
import numpy as np
import requests
from scipy.stats import poisson
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# -----------------------------
# LOAD ENV (SAFE WITH PATH)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "info.env")

load_dotenv(ENV_PATH)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
API_KEY = os.getenv("API_KEY")

# SAFETY CHECK
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, API_KEY]):
    raise ValueError(f"❌ Missing environment variables (checked: {ENV_PATH})")

# -----------------------------
# DATABASE
# -----------------------------
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True
)

# -----------------------------
# API CONFIG
# -----------------------------
HEADERS = {"X-Auth-Token": API_KEY}
BASE_URL = "https://api.football-data.org/v4"

# -----------------------------
# LEAGUES
# -----------------------------
LEAGUE_CODES = {
    "Premier League": "PL",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "La Liga": "PD",
    "Eredivisie": "DED",
    "Primeira Liga": "PPL",
    "Championship": "ELC",
    "Ligue 1": "FL1"
}

# -----------------------------
# TEAM NAME FIX
# -----------------------------
TEAM_NAME_MAP = {
    "1. FC Heidenheim 1846": "FC Heidenheim 1846",
    "1. FC Köln": "FC Köln",
    "1. FC Union Berlin": "FC Union Berlin",
    "1. FSV Mainz 05": "FSV Mainz 05"
}

def fix_team_name(name):
    return TEAM_NAME_MAP.get(name, name)

# -----------------------------
# SQL FUNCTIONS
# -----------------------------
def get_last_matchday(league):
    query = text("""
        SELECT MAX(matchday) as last_matchday
        FROM matches
        WHERE league = :league
    """)

    df = pd.read_sql(query, engine, params={"league": league})
    val = df.iloc[0, 0]

    return int(val) if pd.notna(val) else None

# -----------------------------
# TEAM STATS
# -----------------------------
def get_team_stats_ft(league):
    query = text("""
        SELECT *
        FROM team_attack_defense
        WHERE league_name = :league
    """)

    df = pd.read_sql(query, engine, params={"league": league})
    df.columns = df.columns.str.lower()

    return df.set_index("team_name")


def get_team_stats_ht(league):
    query = text("""
        SELECT *
        FROM team_attack_defense_ht
        WHERE league_name = :league
    """)

    df = pd.read_sql(query, engine, params={"league": league})
    df.columns = df.columns.str.lower()

    return df.set_index("team_name")

# -----------------------------
# FIXTURES
# -----------------------------
def get_next_fixtures(league, matchday):
    code = LEAGUE_CODES[league]

    url = f"{BASE_URL}/competitions/{code}/matches"
    params = {"matchday": matchday}

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)

        if r.status_code != 200:
            print(f"API error for {league}: {r.status_code}")
            return pd.DataFrame()

        matches = r.json().get("matches", [])

        return pd.DataFrame([{
            "home_team": fix_team_name(m["homeTeam"]["name"]),
            "away_team": fix_team_name(m["awayTeam"]["name"])
        } for m in matches])

    except Exception as e:
        print(f"Request failed for {league}: {e}")
        return pd.DataFrame()

# -----------------------------
# POISSON MATRIX
# -----------------------------
def poisson_matrix(exp_home, exp_away, max_goals=5):
    matrix = np.zeros((max_goals + 1, max_goals + 1))

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            matrix[i, j] = poisson.pmf(i, exp_home) * poisson.pmf(j, exp_away)

    return matrix

# -----------------------------
# PROBABILITIES
# -----------------------------
def ft_probs(matrix):
    home = np.sum(np.tril(matrix, -1))
    draw = np.sum(np.diag(matrix))
    away = np.sum(np.triu(matrix, 1))

    over_2_5 = np.sum(matrix) - np.sum(matrix[:2, :2])

    return home, draw, away, over_2_5


def ht_probs(matrix):
    home = np.sum(np.tril(matrix, -1))
    draw = np.sum(np.diag(matrix))
    away = np.sum(np.triu(matrix, 1))

    over_0_5 = np.sum(matrix) - matrix[0, 0]

    return home, draw, away, over_0_5

# -----------------------------
# EXPECTED GOALS
# -----------------------------
def expected_goals(home, away):
    exp_home = home["avg_home_goals_scored"] * away["avg_away_goals_conceded"]
    exp_away = away["avg_away_goals_scored"] * home["avg_home_goals_conceded"]

    return exp_home, exp_away

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_predictions():
    results = []

    for league in LEAGUE_CODES.keys():
        print(f"\nProcessing {league}")

        last_matchday = get_last_matchday(league)

        if last_matchday is None:
            print("No matchday data")
            continue

        fixtures = get_next_fixtures(league, last_matchday + 1)

        if fixtures.empty:
            print("No fixtures found")
            continue

        stats_ft = get_team_stats_ft(league)
        stats_ht = get_team_stats_ht(league)

        for _, row in fixtures.iterrows():
            home = row["home_team"]
            away = row["away_team"]

            if home not in stats_ft.index or away not in stats_ft.index:
                print(f"Missing FT stats: {home} vs {away}")
                continue

            if home not in stats_ht.index or away not in stats_ht.index:
                print(f"Missing HT stats: {home} vs {away}")
                continue

            # -------- FULL TIME --------
            exp_home_ft, exp_away_ft = expected_goals(
                stats_ft.loc[home], stats_ft.loc[away]
            )

            matrix_ft = poisson_matrix(exp_home_ft, exp_away_ft)
            h, d, a, over25 = ft_probs(matrix_ft)

            # -------- HALF TIME --------
            exp_home_ht, exp_away_ht = expected_goals(
                stats_ht.loc[home], stats_ht.loc[away]
            )

            matrix_ht = poisson_matrix(exp_home_ht, exp_away_ht)
            h_ht, d_ht, a_ht, over05 = ht_probs(matrix_ht)

            results.append({
                "league": league,
                "home_team": home,
                "away_team": away,

                # FT
                "ft_exp_home": round(exp_home_ft, 2),
                "ft_exp_away": round(exp_away_ft, 2),
                "ft_home_win": round(h * 100, 2),
                "ft_draw": round(d * 100, 2),
                "ft_away_win": round(a * 100, 2),
                "ft_over_2_5": round(over25 * 100, 2),
                "ft_under_2_5": round((1 - over25) * 100, 2),

                # HT
                "ht_exp_home": round(exp_home_ht, 2),
                "ht_exp_away": round(exp_away_ht, 2),
                "ht_home_win": round(h_ht * 100, 2),
                "ht_draw": round(d_ht * 100, 2),
                "ht_away_win": round(a_ht * 100, 2),
                "ht_over_0_5": round(over05 * 100, 2),
                "ht_under_0_5": round((1 - over05) * 100, 2)
            })

    return pd.DataFrame(results)

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    df = run_predictions()

    print("\nPredictions generated:\n")
    print(df.head())

    #Save in Data/
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", "predictions_all.csv")
    df.to_csv(file_path, index=False)

    print(f"\nSaved to {file_path}")