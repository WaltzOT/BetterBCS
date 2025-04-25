import sqlite3
import pandas as pd
from scipy.stats import beta
import numpy as np
import csv
contrib_log = open("feature_contributions_log.csv", "w", newline='')
contrib_writer = csv.writer(contrib_log)
contrib_writer.writerow(["season", "week", "game_id", "feature", "contribution"])

DECAY_RATE = 0.95
FIRST_TRAINING_WEEK = 4

# Define your stat-based Beta priors
# priors = {
#     'home_rolling_points_scored': (3, 2),
#     'home_rolling_points_allowed': (2, 6),
#     'home_rolling_total_yards_for': (2, 2),
#     'home_rolling_total_yards_against': (1, 1),
#     'home_rolling_elo': (6, 2),

#     'away_rolling_points_scored': (2, 3),
#     'away_rolling_points_allowed': (6, 2),
#     'away_rolling_total_yards_for': (1, 1),
#     'away_rolling_total_yards_against': (3, 2),
#     'away_rolling_elo': (2, 6),

#     'home_field': (6, 4)
# }
priors = {
    'delta_rolling_points_scored': (3, 2),
    'delta_rolling_points_allowed': (2, 6),
    'delta_rolling_total_yards_for': (2, 2),
    'delta_rolling_total_yards_against': (1, 1),
    'delta_rolling_elo': (6, 2),
    'home_field': (6, 4),
    'matchup_home_rolling_points_scored': (3, 2),
    'matchup_away_rolling_points_scored': (2, 3),
    'matchup_home_rolling_total_yards_for': (4, 2),
    'matchup_away_rolling_total_yards_for': (2, 4),
}


# Initialize default Beta(1, 1) for anything not defined above
all_features = set(priors.keys())
def get_prior(name):
    return priors.get(name, (1, 1))

# Load game and stat data
def load_game_data(db_path):
    conn = sqlite3.connect(db_path)
    games = pd.read_sql_query("SELECT * FROM games ORDER BY season, week", conn)
    stats = pd.read_sql_query("SELECT * FROM rolling_team_stats", conn)
    conn.close()
    return games, stats

# Get stats for a given team and week
def get_team_stats(team_id, season, week, stats):
    row = stats[(stats['team_id'] == team_id) & (stats['season'] == season) & (stats['week'] == week)]
    if not row.empty:
        return row.iloc[0].to_dict()
    return None


# Bayesian scoring function
def score_team(features, posteriors):
    score = 0
    contributions = {}
    for f, value in features.items():
        if value is None or pd.isna(value): continue
        a, b = posteriors.get(f, get_prior(f))
        weight = beta.mean(a, b)
        contrib = weight * value
        contributions[f] = contrib
        score += contrib
    return score, contributions


# Update posteriors based on result
def update_posteriors(posteriors, winning_features, losing_features, confidence=1.0):

    for f, win_val in winning_features.items():
        lose_val = losing_features.get(f, 0)
        if win_val is None or pd.isna(win_val): continue
        if lose_val is None or pd.isna(lose_val): continue

        diff = win_val - lose_val
        a, b = posteriors.get(f, get_prior(f))

        if diff > 0:
            # Soft update based on confidence level
            posteriors[f] = (a + confidence, b + (1 - confidence))
        elif diff < 0:
            posteriors[f] = (a + (1 - confidence), b + confidence)
        # If no difference, no update


# Main training loop
def run_bayesian_predictor(db_path):
    games, stats = load_game_data(db_path)

    posteriors = {f: get_prior(f) for f in all_features}
    correct = 0
    total = 0

    for (season, week), week_games in games.groupby(["season", "week"]):
        if week < 4:
            continue  # Skip training on Weeks 0, 1, 2 — not enough rolling data

        print(f"\n Season {season}, Week {week}")

        for _, game in week_games.iterrows():
            if pd.isna(game['score_home']) or pd.isna(game['score_away']):
                continue

            home_stats = get_team_stats(game['home_team_id'], season, week, stats)
            away_stats = get_team_stats(game['away_team_id'], season, week, stats)
            if home_stats is None or away_stats is None:
                continue

            # Pull opponent stats for delta matchup logic
            opp_home = away_stats  # opponent of home team is away
            opp_away = home_stats  # opponent of away team is home



            # Only use regular season games for training
            is_regular = game['game_type'] == 'regular'
            is_postseason = not is_regular

            feature_keys = [
                'rolling_points_scored',
                'rolling_points_allowed',
                'rolling_total_yards_for',
                'rolling_total_yards_against',
                'rolling_elo'
            ]

            relative_feats = {}

            for k in feature_keys:
                home_val = home_stats.get(k)
                away_val = away_stats.get(k)
                opp_home_val = opp_home.get(k.replace('for', 'against'))  # e.g., points_for vs. points_allowed
                opp_away_val = opp_away.get(k.replace('for', 'against'))

                if home_val is not None and away_val is not None:
                    relative_feats[f"delta_{k}"] = home_val - away_val

                # Add team vs. opponent defensive matchup feature
                if home_val is not None and opp_home_val is not None:
                    relative_feats[f"matchup_home_{k}"] = home_val - opp_home_val

                if away_val is not None and opp_away_val is not None:
                    relative_feats[f"matchup_away_{k}"] = away_val - opp_away_val

            # Add home field edge
            relative_feats["home_field"] = 1.0  # always 1.0 when home


            # home_feats['home_field'] = 1.0
            # away_feats['home_field'] = 0.0

            score_home, contribs = score_team(relative_feats, posteriors)
            score_away = 0



            predicted_winner = 'home' if score_home > score_away else 'away'
            actual_winner = 'home' if game['score_home'] > game['score_away'] else 'away'

            correct += (predicted_winner == actual_winner)
            total += 1

            print(f"  Game: {game['home_team_id']} vs {game['away_team_id']} | "
                  f"Predicted: {predicted_winner}, Actual: {actual_winner} | "
                  f"Score(H/A): {score_home:.2f}/{score_away:.2f}")

            # Train only on regular season outcomes
            if is_regular:
                score_diff = abs(score_home - score_away)
                confidence = min(score_diff, 1.0)

                # Apply decay: newer weeks = stronger updates
                weeks_since_start = week - FIRST_TRAINING_WEEK
                decay_factor = DECAY_RATE ** weeks_since_start
                confidence *= decay_factor


                if actual_winner == 'home':
                    update_posteriors(posteriors, relative_feats, {}, confidence=confidence)
                else:
                    flipped = {k: -v for k, v in relative_feats.items()}
                    update_posteriors(posteriors, flipped, {}, confidence=confidence)
            for feat, val in contribs.items():
                contrib_writer.writerow([season, week, game['game_id'], feat, val])

            # top = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            # print(" Top 5 contributing features:")
            # for feat, val in top:
            #     print(f"   - {feat}: {val:+.2f}")


        if total > 0:
            print(f" Accuracy up to this point: {correct}/{total} = {correct / total:.2%}")
        else:
            print("  No games processed this week (missing data or Week 0?)")


# Run the full loop
run_bayesian_predictor("../db_management/cfb_stats.db")
contrib_log.close()
