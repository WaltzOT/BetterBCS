import sqlite3
import pandas as pd

def print_weekly_top_elo(db_path):
    conn = sqlite3.connect(db_path)

    # Load data
    elo = pd.read_sql_query("""
        SELECT team_id, season, week, rolling_elo
        FROM rolling_team_stats
        WHERE rolling_elo IS NOT NULL
    """, conn)

    teams = pd.read_sql_query("SELECT * FROM teams", conn)

    # Merge to get team names
    elo = elo.merge(teams, on='team_id', how='left')

    # Sort and print top 10 for each week
    print("\n[OK] Weekly Top 10 Elo Ratings by Season/Week:\n")
    for (season, week), group in elo.groupby(['season', 'week']):
        top10 = group.sort_values(by='rolling_elo', ascending=False).head(10).reset_index(drop=True)
        top10['rank'] = top10.index + 1
        top10 = top10[['season', 'week', 'rank', 'team_name', 'rolling_elo']]

        print(f"[Loading] Season {season}, Week {week}")
        print(top10.to_string(index=False))
        print("-" * 50)

    conn.close()

# Run it
print_weekly_top_elo("../db_management/cfb_stats.db")
