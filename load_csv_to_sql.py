import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# ----------------------------
# CONFIG
# ----------------------------

INITIAL_LOAD = True  # True for first run, False for weekly updates


def load_config():
    load_dotenv("info.env")

    config = {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME")
    }

    missing = [k for k, v in config.items() if not v]

    if missing:
        raise ValueError(f"Missing environment variables: {missing}")

    return config


# ----------------------------
# ENGINE
# ----------------------------

def create_db_engine(config):
    engine = create_engine(
        f"mysql+pymysql://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['database']}",
        pool_pre_ping=True
    )

    print("✅ Connected to MySQL")
    return engine


# ----------------------------
# LOAD DATA
# ----------------------------

def load_data(file_path):
    df = pd.read_csv(file_path)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(subset=["date", "home_team", "away_team", "league"])

    df = df.drop_duplicates(
        subset=["date", "home_team", "away_team", "league"]
    )

    print(f"📄 Loaded {len(df)} clean rows")

    return df


# ----------------------------
# REFRESH DATABASE
# ----------------------------

def refresh_all(df, engine):

    # ----------------------------
    # TEMP TABLE
    # ----------------------------
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS temp_matches"))

    df.to_sql("temp_matches", con=engine, if_exists="replace", index=False)

    with engine.begin() as conn:

        # ----------------------------
        # INITIAL LOAD ONLY
        # ----------------------------
        if INITIAL_LOAD:
            print("🔵 INITIAL LOAD MODE")

            # TEAMS
            conn.execute(text("""
                INSERT IGNORE INTO teams_c (team_name)
                SELECT DISTINCT home_team FROM temp_matches
                UNION
                SELECT DISTINCT away_team FROM temp_matches;
            """))

            # LEAGUES
            conn.execute(text("""
                INSERT IGNORE INTO leagues_c (league_name)
                SELECT DISTINCT league FROM temp_matches;
            """))

            # SEASONS
            conn.execute(text("""
                INSERT IGNORE INTO seasons_c (season_year, league_id)
                SELECT DISTINCT t.season, l.league_id
                FROM temp_matches t
                JOIN leagues_c l ON t.league = l.league_name
                WHERE t.season IS NOT NULL;
            """))

        else:
            print("🟡 WEEKLY UPDATE MODE (skip dimension tables)")

        # ----------------------------
        # MATCHES INFO
        # ----------------------------
        conn.execute(text("""
            INSERT IGNORE INTO matches_info (
                season_id, match_datetime, home_team_id, away_team_id,
                home_goals_ht, away_goals_ht, home_goals_ft, away_goals_ft,
                matchday, over_under_ht, over_under_ft
            )
            SELECT DISTINCT
                s.season_id,
                t.date,
                ht.team_id,
                at.team_id,
                t.home_score_ht,
                t.away_score_ht,
                t.home_score_ft,
                t.away_score_ft,
                t.matchday,
                t.over_under_ht,
                t.over_under_ft
            FROM temp_matches t
            JOIN teams_c ht ON t.home_team = ht.team_name
            JOIN teams_c at ON t.away_team = at.team_name
            JOIN leagues_c l ON t.league = l.league_name
            JOIN seasons_c s
                ON t.season = s.season_year
                AND s.league_id = l.league_id;
        """))

        print("✅ matches_info updated")

        # ----------------------------
        # MATCHES TABLE
        # ----------------------------
        conn.execute(text("""
            INSERT IGNORE INTO matches (
                date, matchday, home_team, away_team,
                home_score_ht, away_score_ht, home_score_ft, away_score_ft,
                final_score, final_result, league, season,
                over_under_ht, over_under_ft
            )
            SELECT DISTINCT
                m.match_datetime,
                m.matchday,
                ht.team_name,
                at.team_name,
                m.home_goals_ht,
                m.away_goals_ht,
                m.home_goals_ft,
                m.away_goals_ft,
                CONCAT(m.home_goals_ft, '-', m.away_goals_ft),
                CASE
                    WHEN m.home_goals_ft > m.away_goals_ft THEN 'H'
                    WHEN m.home_goals_ft < m.away_goals_ft THEN 'A'
                    ELSE 'D'
                END,
                l.league_name,
                s.season_year,
                m.over_under_ht,
                m.over_under_ft
            FROM matches_info m
            JOIN teams_c ht ON m.home_team_id = ht.team_id
            JOIN teams_c at ON m.away_team_id = at.team_id
            JOIN seasons_c s ON m.season_id = s.season_id
            JOIN leagues_c l ON s.league_id = l.league_id;
        """))

        print("✅ matches updated")

        print("🚀 DATABASE REFRESH COMPLETE")


# ----------------------------
# MAIN
# ----------------------------

def main():
    try:
        config = load_config()
        engine = create_db_engine(config)

        df = load_data("data/all_leagues_2025.csv")

        refresh_all(df, engine)

        print("\n✅ SUCCESS")

    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    main()