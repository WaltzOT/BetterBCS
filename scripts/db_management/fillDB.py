import sqlite3
import pandas as pd

DB_PATH = "cfb_stats.db"
DATA_PATH = "../../data/cfb_box-scores_2002-2024.xlsx"
SHEET_NAME = "cleaned"

def safe_int(val, default=0):
    try: return int(val) if pd.notnull(val) else default
    except: return default

def safe_float(val, default=0.0):
    try: return float(val) if pd.notnull(val) else default
    except: return default

def insert_data():
    df = pd.read_excel(DATA_PATH, sheet_name=SHEET_NAME)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insert unique teams
    teams = pd.unique(df[['home', 'away']].values.ravel())
    team_id_map = {}
    for team in teams:
        cur.execute("INSERT OR IGNORE INTO teams (team_name) VALUES (?)", (team,))
        cur.execute("SELECT team_id FROM teams WHERE team_name = ?", (team,))
        team_id_map[team] = cur.fetchone()[0]

    # Insert games + stats
    for _, row in df.iterrows():
        home_id = team_id_map[row['home']]
        away_id = team_id_map[row['away']]

        cur.execute("""
            INSERT OR IGNORE INTO games (
                season, week, game_type, home_team_id, away_team_id,
                score_home, score_away,
                q1_home, q2_home, q3_home, q4_home, ot_home,
                q1_away, q2_away, q3_away, q4_away, ot_away
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            safe_int(row['season']), safe_int(row['week']), row['game_type'],
            home_id, away_id,
            safe_int(row['score_home']), safe_int(row['score_away']),
            safe_int(row['q1_home']), safe_int(row['q2_home']), safe_int(row['q3_home']),
            safe_int(row['q4_home']), safe_int(row.get('ot_home', 0)),
            safe_int(row['q1_away']), safe_int(row['q2_away']), safe_int(row['q3_away']),
            safe_int(row['q4_away']), safe_int(row.get('ot_away', 0))
        ))

        cur.execute("SELECT game_id FROM games WHERE season=? AND week=? AND home_team_id=? AND away_team_id=?",
                    (safe_int(row['season']), safe_int(row['week']), home_id, away_id))
        game_id = cur.fetchone()[0]

        # Insert team stats (home)
        cur.execute("""
            INSERT OR REPLACE INTO team_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, home_id, True,
            safe_int(row['first_downs_home']), safe_int(row['third_down_comp_home']), safe_int(row['third_down_att_home']),
            safe_int(row['fourth_down_comp_home']), safe_int(row['fourth_down_att_home']),
            safe_int(row['pass_comp_home']), safe_int(row['pass_att_home']), safe_int(row['pass_yards_home']),
            safe_int(row['rush_att_home']), safe_int(row['rush_yards_home']), safe_int(row['total_yards_home']),
            safe_int(row['fum_home']), safe_int(row['int_home']),
            safe_int(row['pen_num_home']), safe_int(row['pen_yards_home']),
            safe_float(row['possession_home'])
        ))

        # Insert team stats (away)
        cur.execute("""
            INSERT OR REPLACE INTO team_game_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, away_id, False,
            safe_int(row['first_downs_away']), safe_int(row['third_down_comp_away']), safe_int(row['third_down_att_away']),
            safe_int(row['fourth_down_comp_away']), safe_int(row['fourth_down_att_away']),
            safe_int(row['pass_comp_away']), safe_int(row['pass_att_away']), safe_int(row['pass_yards_away']),
            safe_int(row['rush_att_away']), safe_int(row['rush_yards_away']), safe_int(row['total_yards_away']),
            safe_int(row['fum_away']), safe_int(row['int_away']),
            safe_int(row['pen_num_away']), safe_int(row['pen_yards_away']),
            safe_float(row['possession_away'])
        ))

    conn.commit()
    conn.close()
    print("Data inserted successfully.")

if __name__ == "__main__":
    insert_data()
