import sqlite3
import pandas as pd

conn = sqlite3.connect("../db_management/cfb_stats.db")
df = pd.read_sql_query("SELECT * FROM rolling_team_stats WHERE season = 2004 AND week = 4", conn)
conn.close()

print(df.head())
