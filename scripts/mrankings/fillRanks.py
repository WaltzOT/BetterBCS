import sqlite3
import pandas as pd

def compute_rolling_team_stats(db_path, verbose=True):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    games = pd.read_sql_query("""
        SELECT * FROM games
        WHERE game_type = 'regular'
        ORDER BY season, week
    """, conn)

    team_game_stats = pd.read_sql_query("SELECT * FROM team_game_stats", conn)

    cursor.execute("DELETE FROM rolling_team_stats")
    conn.commit()

    rolling_stats = [
        "rolling_pass_yards_for", "rolling_rush_yards_for", "rolling_total_yards_for", "rolling_points_scored",
        "rolling_pass_yards_against", "rolling_rush_yards_against", "rolling_total_yards_against", "rolling_points_allowed",
        "rolling_elo"
    ]
    rank_fields = [
        "pass_yards_for_rank", "rush_yards_for_rank", "total_yards_for_rank", "points_scored_rank",
        "pass_yards_against_rank", "rush_yards_against_rank", "total_yards_against_rank", "points_allowed_rank",
        "elo_rank"
    ]

    for (season, week), week_games in games.groupby(["season", "week"]):
        if verbose:
            print(f"\n[LOADING] Processing Season {season}, Week {week}")

        team_ids = pd.concat([
            week_games[["home_team_id"]].rename(columns={"home_team_id": "team_id"}),
            week_games[["away_team_id"]].rename(columns={"away_team_id": "team_id"})
        ]).drop_duplicates()['team_id'].tolist()

        week_data = []

        for team_id in team_ids:
            if verbose:
                print(f"  [LOADING] Team {team_id}")

            prior_games = games[
                ((games['home_team_id'] == team_id) | (games['away_team_id'] == team_id)) &
                ((games['season'] < season) | ((games['season'] == season) & (games['week'] < week)))
            ]
            if prior_games.empty:
                if verbose:
                    print("     [ERROR]  No prior games — skipping.")
                continue

            game_ids = prior_games['game_id'].tolist()
            team_stats = team_game_stats[
                (team_game_stats['team_id'] == team_id) &
                (team_game_stats['game_id'].isin(game_ids))
            ]

            opponent_stats_list = []
            for gid in game_ids:
                game_row = prior_games[prior_games['game_id'] == gid].iloc[0]
                opponent_id = game_row['away_team_id'] if game_row['home_team_id'] == team_id else game_row['home_team_id']
                opp_stats = team_game_stats[
                    (team_game_stats['game_id'] == gid) &
                    (team_game_stats['team_id'] == opponent_id)
                ]
                if not opp_stats.empty:
                    opponent_stats_list.append(opp_stats.iloc[0])

            if team_stats.empty or not opponent_stats_list:
                if verbose:
                    print("     [ERROR]  Missing stats — skipping.")
                continue

            opponent_stats = pd.DataFrame(opponent_stats_list)

            team_games = prior_games.copy()
            team_games['is_home'] = team_games['home_team_id'] == team_id
            team_games['points_scored'] = team_games.apply(lambda row:
                row['score_home'] if row['is_home'] else row['score_away'], axis=1)
            team_games['points_allowed'] = team_games.apply(lambda row:
                row['score_away'] if row['is_home'] else row['score_home'], axis=1)

            row = {
                'team_id': team_id,
                'season': season,
                'week': week,
                'rolling_pass_yards_for': team_stats['pass_yards'].mean(),
                'rolling_rush_yards_for': team_stats['rush_yards'].mean(),
                'rolling_total_yards_for': team_stats['total_yards'].mean(),
                'rolling_points_scored': team_games['points_scored'].mean(),
                'rolling_pass_yards_against': opponent_stats['pass_yards'].mean(),
                'rolling_rush_yards_against': opponent_stats['rush_yards'].mean(),
                'rolling_total_yards_against': opponent_stats['total_yards'].mean(),
                'rolling_points_allowed': team_games['points_allowed'].mean(),
                'rolling_elo': 1500.0  # placeholder
            }

            week_data.append(row)

        week_df = pd.DataFrame(week_data)

        if week_df.empty:
            if verbose:
                print("  [ERROR]  No valid teams to rank this week.")
            continue

        for stat, rank in zip(rolling_stats, rank_fields):
            week_df[rank] = week_df[stat].rank(ascending=False, method='min')

        for _, row in week_df.iterrows():
            cursor.execute(f"""
                INSERT INTO rolling_team_stats (
                    team_id, season, week,
                    rolling_pass_yards_for, rolling_rush_yards_for, rolling_total_yards_for, rolling_points_scored,
                    rolling_pass_yards_against, rolling_rush_yards_against, rolling_total_yards_against, rolling_points_allowed,
                    rolling_elo,
                    pass_yards_for_rank, rush_yards_for_rank, total_yards_for_rank, points_scored_rank,
                    pass_yards_against_rank, rush_yards_against_rank, total_yards_against_rank, points_allowed_rank,
                    elo_rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['team_id'], row['season'], row['week'],
                row['rolling_pass_yards_for'], row['rolling_rush_yards_for'], row['rolling_total_yards_for'], row['rolling_points_scored'],
                row['rolling_pass_yards_against'], row['rolling_rush_yards_against'], row['rolling_total_yards_against'], row['rolling_points_allowed'],
                row['rolling_elo'],
                row['pass_yards_for_rank'], row['rush_yards_for_rank'], row['total_yards_for_rank'], row['points_scored_rank'],
                row['pass_yards_against_rank'], row['rush_yards_against_rank'], row['total_yards_against_rank'], row['points_allowed_rank'],
                row['elo_rank']
            ))

        conn.commit()

        if verbose:
            print("  [OK] Weekly stats and ranks updated:")
            print(week_df[['team_id', 'rolling_total_yards_for', 'total_yards_for_rank']].sort_values(by='total_yards_for_rank').head())

    conn.close()
    print("\n[OK] Rolling stats and ranks successfully computed across all seasons and weeks.")

# Run it
compute_rolling_team_stats("../db_management/cfb_stats.db", verbose=True)
