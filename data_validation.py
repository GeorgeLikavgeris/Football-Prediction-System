import logging
from pathlib import Path

import pandas as pd

# -----------------------------
# CONFIGURATION
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "data" / "all_leagues_2026.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

REQUIRED_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score_ft",
    "away_score_ft",
    "home_score_ht",
    "away_score_ht",
    "league",
    "season",
    "final_result",
]

SCORE_COLUMNS = [
    "home_score_ft",
    "away_score_ft",
    "home_score_ht",
    "away_score_ht",
]


def main():

    # -----------------------------
    # 1. LOAD DATA
    # -----------------------------
    if not CSV_FILE.exists():
        logging.error("CSV file not found: %s", CSV_FILE)
        return

    try:
        df = pd.read_csv(CSV_FILE)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        logging.error("Could not read CSV file: %s", exc)
        return

    print("\n" + "=" * 45)
    print("FOOTBALL DATA VALIDATION")
    print("=" * 45)

    print(f"\nDataset: {CSV_FILE.name}")
    print(f"Total rows: {len(df)}")

    if df.empty:
        logging.error("Dataset is empty.")
        return

    # -----------------------------
    # 2. COLUMN VALIDATION
    # -----------------------------
    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    print("\n[1] COLUMN VALIDATION")

    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        logging.error("Cannot continue validation.")
        return

    print("All required columns are present.")

    # -----------------------------
    # 3. MISSING VALUES
    # -----------------------------
    print("\n[2] MISSING VALUES")

    missing = df.isnull().sum()
    missing = missing[missing > 0]

    if missing.empty:
        print("No missing values found.")
    else:
        print(missing.to_string())
        print(
            "\nNote: Some optional fields, such as matchday, "
            "may legitimately be missing."
        )

    critical_columns = [
        "date",
        "home_team",
        "away_team",
        "home_score_ft",
        "away_score_ft",
        "home_score_ht",
        "away_score_ht",
        "league",
    ]

    missing_critical = df[critical_columns].isnull().any(axis=1)

    print(
        f"Rows with missing critical values: "
        f"{int(missing_critical.sum())}"
    )

    # -----------------------------
    # 4. DUPLICATE MATCHES
    # -----------------------------
    print("\n[3] DUPLICATE MATCHES")

    duplicate_mask = df.duplicated(
        subset=["date", "home_team", "away_team", "league"],
        keep=False,
    )

    duplicate_count = int(
        df.duplicated(
            subset=["date", "home_team", "away_team", "league"]
        ).sum()
    )

    print(
        "Duplicate rows beyond the first occurrence: "
        f"{duplicate_count}"
    )

    if duplicate_mask.any():
        print("\nDuplicate match records:")
        print(
            df.loc[
                duplicate_mask,
                ["date", "home_team", "away_team", "league"],
            ]
            .sort_values(["league", "date"])
            .to_string(index=False)
        )
    else:
        print("No duplicate matches found.")

    # -----------------------------
    # 5. DATE VALIDATION
    # -----------------------------
    print("\n[4] DATE VALIDATION")

    parsed_dates = pd.to_datetime(
        df["date"],
        errors="coerce",
        utc=True,
    )

    invalid_dates = parsed_dates.isna()

    print(f"Invalid dates: {int(invalid_dates.sum())}")

    # -----------------------------
    # 6. SCORE VALIDATION
    # -----------------------------
    print("\n[5] SCORE VALIDATION")

    numeric_scores = df[SCORE_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce",
    )

    invalid_numeric = numeric_scores.isna().any(axis=1)

    negative_scores = (numeric_scores < 0).any(axis=1)

    non_integer_scores = (
        numeric_scores.notna()
        & ((numeric_scores % 1) != 0)
    ).any(axis=1)

    # Half-time goals cannot exceed full-time goals.
    ht_exceeds_ft = (
        (
            numeric_scores["home_score_ht"]
            > numeric_scores["home_score_ft"]
        )
        |
        (
            numeric_scores["away_score_ht"]
            > numeric_scores["away_score_ft"]
        )
    )

    invalid_scores = (
        invalid_numeric
        | negative_scores
        | non_integer_scores
        | ht_exceeds_ft
    )

    print(
        f"Missing or non-numeric scores: "
        f"{int(invalid_numeric.sum())}"
    )
    print(f"Negative scores: {int(negative_scores.sum())}")
    print(f"Non-integer scores: {int(non_integer_scores.sum())}")
    print(
        "Half-time score exceeds full-time score: "
        f"{int(ht_exceeds_ft.sum())}"
    )
    print(
        f"Rows with at least one score issue: "
        f"{int(invalid_scores.sum())}"
    )

    # -----------------------------
    # 7. MATCH RESULT VALIDATION
    # -----------------------------
    print("\n[6] RESULT VALIDATION")

    home_ft = numeric_scores["home_score_ft"]
    away_ft = numeric_scores["away_score_ft"]

    expected_result = pd.Series(
        index=df.index,
        dtype="object",
    )

    valid_ft = home_ft.notna() & away_ft.notna()

    expected_result.loc[
        valid_ft & (home_ft > away_ft)
    ] = "H"

    expected_result.loc[
        valid_ft & (home_ft < away_ft)
    ] = "A"

    expected_result.loc[
        valid_ft & (home_ft == away_ft)
    ] = "D"

    result_mismatch = (
        valid_ft
        & df["final_result"].ne(expected_result)
    )

    print(
        f"Inconsistent final results: "
        f"{int(result_mismatch.sum())}"
    )

    # -----------------------------
    # 8. LEAGUE COVERAGE
    # -----------------------------
    print("\n[7] MATCHES PER LEAGUE")

    print(df["league"].value_counts(dropna=False).to_string())

    # -----------------------------
    # 9. SEASON CHECK
    # -----------------------------
    print("\n[8] SEASON CHECK")

    season_values = pd.to_numeric(
        df["season"],
        errors="coerce",
    )

    unexpected_seasons = (
        season_values.isna()
        | (season_values != 2026)
    )

    print(
        "Rows not marked as season 2026: "
        f"{int(unexpected_seasons.sum())}"
    )

    # -----------------------------
    # 10. FINAL SUMMARY
    # -----------------------------
    issue_counts = {
        "Missing critical values": int(missing_critical.sum()),
        "Duplicate matches": duplicate_count,
        "Invalid dates": int(invalid_dates.sum()),
        "Invalid score rows": int(invalid_scores.sum()),
        "Inconsistent results": int(result_mismatch.sum()),
        "Unexpected season": int(unexpected_seasons.sum()),
    }

    total_issues = sum(issue_counts.values())

    print("\n" + "=" * 45)
    print("VALIDATION SUMMARY")
    print("=" * 45)

    for issue, count in issue_counts.items():
        print(f"{issue}: {count}")

    if total_issues == 0:
        print("\nVALIDATION PASSED")
        logging.info("No data quality issues detected.")
    else:
        print("\nVALIDATION NEEDS REVIEW")
        logging.warning(
            "Potential data quality issues found. "
            "Review the report before prediction."
        )

    print("\nNo rows were deleted or modified.")


if __name__ == "__main__":
    main()
