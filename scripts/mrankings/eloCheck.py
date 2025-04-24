import sqlite3
import pandas as pd

def print_top10_elo_weekly(db_path):
    conn = sqlite3.connect(db_path)

    # Load rolling stats + team names
    elo = pd.read_sql_query("SELECT * FROM rolling_team_stats", conn)
    teams = pd.read_sql_query("SELECT * FROM teams", conn)

    # Merge in team names
    elo = elo.merge(teams, on="team_id", how="left")

    # Loop over each season and week
    for (season, week), group in elo.groupby(["season", "week"]):
        top10 = group.sort_values(by="rolling_elo", ascending=False).head(10)

        print(f"\n[Loading] Season {season} – Week {week} Top 10 Elo Ratings")
        print(top10[["team_name", "rolling_elo"]].round(1).reset_index(drop=True).to_string(index=False))

    conn.close()

# Run it
print_top10_elo_weekly("../db_management/cfb_stats.db")
