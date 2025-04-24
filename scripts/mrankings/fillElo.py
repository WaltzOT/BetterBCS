import sqlite3
import pandas as pd
import numpy as np

def update_elo_ratings(db_path, base_k=20, decay_factor=0.95, verbose=True):
    conn = sqlite3.connect(db_path)

    # Load all required data
    games = pd.read_sql_query("""
        SELECT * FROM games
        WHERE game_type = 'regular'
        ORDER BY season, week
    """, conn)

    teams = pd.read_sql_query("SELECT * FROM teams", conn)
    ranks = pd.read_sql_query("SELECT * FROM rolling_team_stats", conn)

    elo_history = []

    # Step 1: Loop by season
    for season in sorted(games['season'].unique()):
        if verbose:
            print(f"\n[LOADING] Starting Elo for Season {season}")

        # Step 2: Init Elo per team
        current_elo = {team_id: 1500 for team_id in teams['team_id']}

        season_games = games[games['season'] == season]

        for week in sorted(season_games['week'].unique()):
            week_games = season_games[season_games['week'] == week]

            for _, game in week_games.iterrows():
                home, away = game['home_team_id'], game['away_team_id']
                score_home, score_away = game['score_home'], game['score_away']

                if pd.isna(score_home) or pd.isna(score_away):
                    continue  # Skip incomplete data

                # Step 3: Compute Expected values
                elo_home = current_elo[home]
                elo_away = current_elo[away]

                expected_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
                expected_away = 1 - expected_home

                actual_home = 1 if score_home > score_away else 0
                actual_away = 1 - actual_home

                # Rank difference modifier (better rank → lower number)
                rank_home_off = ranks.query(f"season == {season} and week == {week} and team_id == {home}")['points_scored_rank'].values
                rank_away_def = ranks.query(f"season == {season} and week == {week} and team_id == {away}")['points_allowed_rank'].values

                if len(rank_home_off) > 0 and len(rank_away_def) > 0:
                    rank_diff_mod = ((rank_away_def[0] - rank_home_off[0]) / 25)  # e.g. -1.0 to 1.0 range
                else:
                    rank_diff_mod = 0

                # Week decay
                week_decay = decay_factor ** (week - 1)

                # Final modifier
                k = base_k * week_decay * (1 + rank_diff_mod)

                # Step 4: Elo update
                change_home = k * (actual_home - expected_home)
                change_away = -change_home

                current_elo[home] += change_home
                current_elo[away] += change_away

                # Save elo snapshot
                elo_history.append({
                    'team_id': home,
                    'season': season,
                    'week': week,
                    'rolling_elo': current_elo[home]
                })
                elo_history.append({
                    'team_id': away,
                    'season': season,
                    'week': week,
                    'rolling_elo': current_elo[away]
                })

            if verbose:
                sample = pd.DataFrame([
                    {'team': tid, 'elo': round(e, 1)} for tid, e in current_elo.items()
                ]).sort_values(by='elo', ascending=False).head(3)
                print(f"  [OK] Week {week} top 3 Elos:\n{sample.to_string(index=False)}")

    # Step 5: Write back updated Elo to rolling_team_stats
    elo_df = pd.DataFrame(elo_history)

    for _, row in elo_df.iterrows():
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE rolling_team_stats
            SET rolling_elo = ?
            WHERE team_id = ? AND season = ? AND week = ?
        """, (row['rolling_elo'], row['team_id'], row['season'], row['week']))
    conn.commit()
    conn.close()

    print("\n{SUCCESS] Elo ratings updated for all games.")

# Run it
update_elo_ratings("../db_management/cfb_stats.db", base_k=25, decay_factor=0.97, verbose=True)
