import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import numpy as np
import argparse

DB_PATH = "../db_management/cfb_stats.db"
# Argument parser for reproducibility
parser = argparse.ArgumentParser()
parser.add_argument("--db_path", type=str, default="cfb_stats.db")
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

# Connect to SQLite database
conn = sqlite3.connect(DB_PATH)

# Pull data from DB using relevant rolling stats
query = """
SELECT 
    g.season, g.week, g.home_team_id, g.away_team_id, g.score_home, g.score_away,
    rs1.rolling_total_yards_for AS home_yards,
    rs1.rolling_points_scored AS home_points,
    rs1.rolling_points_allowed AS home_pa,
    rs1.rolling_elo AS home_elo,
    rs2.rolling_total_yards_for AS away_yards,
    rs2.rolling_points_scored AS away_points,
    rs2.rolling_points_allowed AS away_pa,
    rs2.rolling_elo AS away_elo,
    t1.team_name AS home_team_name,
    t2.team_name AS away_team_name
FROM games g
JOIN rolling_team_stats rs1 ON g.home_team_id = rs1.team_id AND g.season = rs1.season AND g.week = rs1.week
JOIN rolling_team_stats rs2 ON g.away_team_id = rs2.team_id AND g.season = rs2.season AND g.week = rs2.week
JOIN teams t1 ON g.home_team_id = t1.team_id
JOIN teams t2 ON g.away_team_id = t2.team_id
WHERE g.game_type = 'regular' AND g.week > 3
"""

raw_df = pd.read_sql_query(query, conn)
conn.close()

# Create target
raw_df["home_win"] = (raw_df["score_home"] > raw_df["score_away"]).astype(int)

# Select features
features = [
    "home_yards", "home_points", "home_pa", "home_elo",
    "away_yards", "away_points", "away_pa", "away_elo"
]

# Split based on seasons
unique_seasons = raw_df["season"].unique()
train_seasons, test_seasons = train_test_split(unique_seasons, test_size=0.3, random_state=args.seed)

train_mask = raw_df["season"].isin(train_seasons)
test_mask = raw_df["season"].isin(test_seasons)

X_train = raw_df.loc[train_mask, features].fillna(0)
y_train = raw_df.loc[train_mask, "home_win"]
X_test = raw_df.loc[test_mask, features].fillna(0)
y_test = raw_df.loc[test_mask, "home_win"]
test_metadata = raw_df.loc[test_mask, ["season", "week", "home_team_id", "away_team_id", "home_team_name", "away_team_name", "score_home", "score_away"]]

# Train random forest
model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=args.seed)
model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)

print(f"\ Random Forest Accuracy: {acc:.2%}\n")

# Print prediction breakdown
results = test_metadata.copy()
results["predicted"] = preds
results["actual"] = y_test.reset_index(drop=True)
results["correct"] = results["predicted"] == results["actual"]

print(" Prediction Results:")
for _, row in results.iterrows():
    outcome = "Correct" if row["correct"] else "Incorrect"
    print(f"Season {row['season']}, Week {row['week']} | {row['home_team_name']} vs {row['away_team_name']} | Predicted: {'Home' if row['predicted'] else 'Away'} | Actual: {'Home' if row['actual'] else 'Away'} | Score(H/A): {row['score_home']}/{row['score_away']} | {outcome}")
