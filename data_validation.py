import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

CSV_FILE = "data/all_leagues_2025.csv"

# -----------------------------
# LOAD DATA
# -----------------------------

df = pd.read_csv(CSV_FILE)

logging.info(f"Loaded dataset: {len(df)} rows")

# -----------------------------
# 1. MISSING VALUES CHECK
# -----------------------------

missing = df.isnull().sum()
missing = missing[missing > 0]

if not missing.empty:
    print("\n⚠️ MISSING VALUES FOUND:")
    print(missing)
else:
    print("\n✅ No missing values found")

# -----------------------------
# 2. DUPLICATES CHECK
# -----------------------------

duplicates = df.duplicated(
    subset=["date", "home_team", "away_team", "league"]
).sum()

print(f"\n🔁 Duplicate matches found: {duplicates}")

# -----------------------------
# 3. DATE VALIDATION
# -----------------------------

df["date"] = pd.to_datetime(df["date"], errors="coerce")

invalid_dates = df["date"].isna().sum()

print(f"\n📅 Invalid dates: {invalid_dates}")

# -----------------------------
# 4. SCORE VALIDATION
# -----------------------------

score_cols = [
    "home_score_ft",
    "away_score_ft",
    "home_score_ht",
    "away_score_ht"
]

invalid_scores = 0

for col in score_cols:
    if col in df.columns:
        invalid_scores += (df[col] < 0).sum()

print(f"\n⚽ Invalid score values: {invalid_scores}")

# -----------------------------
# 5. LEAGUE COVERAGE CHECK
# -----------------------------

print("\n📊 Matches per league:\n")
print(df["league"].value_counts())

# -----------------------------
# 6. FINAL SUMMARY
# -----------------------------

print("\n============================")
print("DATA VALIDATION SUMMARY")
print("============================")

print(f"Total rows: {len(df)}")
print(f"Missing values columns: {len(missing)}")
print(f"Duplicates: {duplicates}")
print(f"Invalid dates: {invalid_dates}")
print(f"Invalid scores: {invalid_scores}")

print("\n✅ Validation completed")