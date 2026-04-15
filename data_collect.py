import requests
import pandas as pd
import logging
import os
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV (SAFE)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "info.env")

load_dotenv(ENV_PATH)

API_TOKEN = os.getenv("API_KEY")

if not API_TOKEN:
    raise ValueError("❌ Missing API_KEY in info.env file")

HEADERS = {"X-Auth-Token": API_TOKEN}
BASE_URL = "https://api.football-data.org/v4"

# -----------------------------
# CONFIG
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

CSV_FILE = "data/all_leagues_2025.csv"
SEASON = 2025

competitions = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "DED": "Eredivisie",
    "ELC": "Championship",
    "PPL": "Primeira Liga"
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
# FETCH MATCHES (WITH SEASON!)
# -----------------------------
def fetch_matches(code):
    url = f"{BASE_URL}/competitions/{code}/matches"

    params = {
        "season": SEASON
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)

        if r.status_code != 200:
            logging.error(f"API error {code} - {r.status_code}")
            return []

        return r.json().get("matches", [])

    except Exception as e:
        logging.error(f"Request failed for {code}: {e}")
        return []

# -----------------------------
# PROCESS MATCHES (FULL DATA)
# -----------------------------
def process(matches, league_name):
    rows = []

    for m in matches:
        if m.get("status") != "FINISHED":
            continue

        home = fix_team_name(m["homeTeam"]["name"])
        away = fix_team_name(m["awayTeam"]["name"])

        # scores
        home_ht = m["score"]["halfTime"]["home"]
        away_ht = m["score"]["halfTime"]["away"]
        home_ft = m["score"]["fullTime"]["home"]
        away_ft = m["score"]["fullTime"]["away"]

        # result
        if home_ft > away_ft:
            result = "H"
        elif home_ft < away_ft:
            result = "A"
        else:
            result = "D"

        total_ht = (home_ht or 0) + (away_ht or 0)
        total_ft = (home_ft or 0) + (away_ft or 0)

        rows.append({
            "date": pd.to_datetime(m.get("utcDate")),
            "matchday": m.get("matchday"),
            "home_team": home,
            "away_team": away,

            "home_score_ht": home_ht,
            "away_score_ht": away_ht,
            "home_score_ft": home_ft,
            "away_score_ft": away_ft,

            "final_score": f"{home_ft}-{away_ft}",
            "final_result": result,

            "league": league_name,
            "season": SEASON,

            "over_under_ht": 1 if total_ht > 1 else 0,
            "over_under_ft": 1 if total_ft > 2 else 0
        })

    return rows

# -----------------------------
# LAST MATCH DATE
# -----------------------------
def get_last_date(matches):
    finished_dates = [
        pd.to_datetime(m["utcDate"])
        for m in matches
        if m.get("status") == "FINISHED"
    ]

    return max(finished_dates) if finished_dates else None

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    all_rows = []

    for code, league in competitions.items():
        logging.info(f"Processing {league}")

        matches = fetch_matches(code)
        rows = process(matches, league)

        all_rows.extend(rows)

        last_date = get_last_date(matches)

        if last_date:
            logging.info(f"{league} LAST MATCH DATE: {last_date.date()}")
        else:
            logging.info(f"{league} NO DATA FOUND")

    df = pd.DataFrame(all_rows)

    # -----------------------------
    # SAVE CSV
    # -----------------------------
    os.makedirs("data", exist_ok=True)
    df.to_csv(CSV_FILE, index=False)

    logging.info("\n✅ DONE - FULL REFRESH COMPLETED")
    logging.info(f"TOTAL MATCHES: {len(df)}")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    main()
    