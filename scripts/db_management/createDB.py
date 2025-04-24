import sqlite3

DB_PATH = "cfb_stats.db"

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS rolling_team_stats;
    DROP TABLE IF EXISTS team_game_stats;
    DROP TABLE IF EXISTS games;
    DROP TABLE IF EXISTS teams;

    CREATE TABLE teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT UNIQUE
    );

    CREATE TABLE games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        season INTEGER,
        week INTEGER,
        game_type TEXT,
        home_team_id INTEGER,
        away_team_id INTEGER,
        score_home INTEGER,
        score_away INTEGER,
        q1_home INTEGER, q2_home INTEGER, q3_home INTEGER, q4_home INTEGER, ot_home INTEGER,
        q1_away INTEGER, q2_away INTEGER, q3_away INTEGER, q4_away INTEGER, ot_away INTEGER,
        UNIQUE(season, week, home_team_id, away_team_id)
    );

    CREATE TABLE team_game_stats (
        game_id INTEGER,
        team_id INTEGER,
        is_home BOOLEAN,
        first_downs INTEGER,
        third_down_comp INTEGER,
        third_down_att INTEGER,
        fourth_down_comp INTEGER,
        fourth_down_att INTEGER,
        pass_comp INTEGER,
        pass_att INTEGER,
        pass_yards INTEGER,
        rush_att INTEGER,
        rush_yards INTEGER,
        total_yards INTEGER,
        fumbles INTEGER,
        interceptions INTEGER,
        pen_num INTEGER,
        pen_yards INTEGER,
        possession_time REAL,
        PRIMARY KEY (game_id, team_id)
    );

    CREATE TABLE rolling_team_stats (
        team_id INTEGER,
        season INTEGER,
        week INTEGER,
        rolling_pass_yards_for REAL,
        rolling_rush_yards_for REAL,
        rolling_total_yards_for REAL,
        rolling_points_scored REAL,
        rolling_pass_yards_against REAL,
        rolling_rush_yards_against REAL,
        rolling_total_yards_against REAL,
        rolling_points_allowed REAL,
        rolling_elo REAL,
        pass_yards_for_rank INTEGER,
        rush_yards_for_rank INTEGER,
        total_yards_for_rank INTEGER,
        points_scored_rank INTEGER,
        pass_yards_against_rank INTEGER,
        rush_yards_against_rank INTEGER,
        total_yards_against_rank INTEGER,
        points_allowed_rank INTEGER,
        elo_rank INTEGER,
        PRIMARY KEY (team_id, season, week)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized and tables created at {DB_PATH}.")

if __name__ == "__main__":
    create_database()
