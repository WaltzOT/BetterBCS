import sqlite3
import pandas as pd

def check_rank_completeness(db_path):
    conn = sqlite3.connect(db_path)

    rank_columns = [
        "pass_yards_for_rank", "rush_yards_for_rank", "total_yards_for_rank", "points_scored_rank",
        "pass_yards_against_rank", "rush_yards_against_rank", "total_yards_against_rank", "points_allowed_rank",
        "elo_rank"
    ]

    # Load everything
    df = pd.read_sql_query("SELECT * FROM rolling_team_stats", conn)

    if df.empty:
        print("[ERROR] No entries found in rolling_team_stats.")
        conn.close()
        return

    # Find rows with missing rank values
    missing_ranks = df[df[rank_columns].isnull().any(axis=1)]

    if missing_ranks.empty:
        print("[OK] All ranks are properly filled out.")
        print(df.head())
    else:
        print("[WARNING] Missing rank values found. First 5 incomplete rows below (all columns):")
        pd.set_option('display.max_columns', None)
        print(missing_ranks.head())
        print(f"\nTotal missing entries: {len(missing_ranks)}")

    conn.close()

# Run it
check_rank_completeness("../db_management/cfb_stats.db")
