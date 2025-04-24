import sqlite3
import pandas as pd

conn = sqlite3.connect("cfb_stats.db")

# View tables
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
print(tables)

# View part of the games table
df = pd.read_sql("SELECT * FROM teams LIMIT 10;", conn)
print(df)

def get_team_week_stats(team_name, season, week, db_path="cfb_stats.db"):
    conn = sqlite3.connect(db_path)

    query = """
    SELECT 
        t.team_name,
        g.season, g.week,
        g.game_type,
        g.score_home, g.score_away,
        s.is_home,
        s.first_downs, s.pass_yards, s.rush_yards, s.total_yards,
        s.fumbles, s.interceptions, s.possession_time
    FROM team_game_stats s
    JOIN teams t ON s.team_id = t.team_id
    JOIN games g ON s.game_id = g.game_id
    WHERE t.team_name = ?
      AND g.season = ?
      AND g.week = ?;
    """
    df = pd.read_sql(query, conn, params=(team_name, season, week))
    conn.close()
    return df

# Example use
df2 = get_team_week_stats("Oregon", 2023, 7)
print(df2)

conn.close()
