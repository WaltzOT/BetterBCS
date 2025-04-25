import sqlite3
import pandas as pd
from sklearn.neural_network import MLPClassifier
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
    g.season, g.week, g.score_home, g.score_away,
    rs1.rolling_total_yards_for AS home_yards,
    rs1.rolling_points_scored AS home_points,
    rs1.rolling_points_allowed AS home_pa,
    rs1.rolling_elo AS home_elo,
    rs2.rolling_total_yards_for AS away_yards,
    rs2.rolling_points_scored AS away_points,
    rs2.rolling_points_allowed AS away_pa,
    rs2.rolling_elo AS away_elo
FROM games g
JOIN rolling_team_stats rs1 ON g.home_team_id = rs1.team_id AND g.season = rs1.season AND g.week = rs1.week
JOIN rolling_team_stats rs2 ON g.away_team_id = rs2.team_id AND g.season = rs2.season AND g.week = rs2.week
WHERE g.game_type = 'regular'
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

# Get train/test weeks
unique_weeks = raw_df["week"].dropna().unique()
train_weeks, test_weeks = train_test_split(unique_weeks, test_size=0.3, random_state=args.seed)

train_mask = raw_df["week"].isin(train_weeks)
test_mask = raw_df["week"].isin(test_weeks)

X_train = raw_df.loc[train_mask, features].fillna(0)
y_train = raw_df.loc[train_mask, "home_win"]
X_test = raw_df.loc[test_mask, features].fillna(0)
y_test = raw_df.loc[test_mask, "home_win"]

# Train neural net
model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=args.seed)
model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f" Neural Network Accuracy: {acc:.2%}")