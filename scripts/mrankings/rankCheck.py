import sqlite3
import pandas as pd

def check_rank_completeness(db_path):
    conn = sqlite3.connect(db_path)

    # Rank columns to check
    rank_columns = [
        "pass_yards_for_rank", "rush_yards_for_rank", "total_yards_for_rank", "points_scored_rank",
        "pass_yards_against_rank", "rush_yards_against_rank", "total_yards_against_rank", "points_allowed_rank",
        "elo_rank"
    ]

    # Load the full data
    df = pd.read_sql_query(
        f"SELECT team_id, season, week, " + ", ".join(rank_columns) + " FROM rolling_team_stats",
        conn
    )

    if df.empty:
        print("[ERROR] The rolling_team_stats table is empty. Cannot show an example week.")
        conn.close()
        return

    # Check for missing rank values
    missing_ranks = df[df[rank_columns].isnull().any(axis=1)]

    if missing_ranks.empty:
        print("[OK] All ranks are properly filled out.")
    else:
        print("[WARNING] Missing rank values found. Here's a preview:")
        print(missing_ranks.head())
        print(f"\nTotal missing entries: {len(missing_ranks)}")
        conn.close()
        return

    # Check if any grouped weeks exist
    grouped = df.groupby(['season', 'week'])
    if not grouped.groups:
        print("[WARNING] No valid season/week combinations found with rank data.")
        conn.close()
        return

    # Show example week (first one in the list)
    sample_key = next(iter(grouped.groups))
    example_week_df = grouped.get_group(sample_key).sort_values(by='elo_rank')

    print(f"\n Example season/week: {sample_key[0]} / Week {sample_key[1]}")
    print(example_week_df[['team_id', *rank_columns]])

    conn.close()

# Run this
check_rank_completeness("../db_management/cfb_stats.db")
