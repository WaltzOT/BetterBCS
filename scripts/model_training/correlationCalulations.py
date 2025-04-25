import sqlite3
import pandas as pd
from scipy.stats import pointbiserialr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def build_feature_matrix(db_path):
    conn = sqlite3.connect(db_path)

    games = pd.read_sql_query("""
        SELECT * FROM games
        WHERE game_type = 'regular'
        ORDER BY season, week
    """, conn)

    stats = pd.read_sql_query("SELECT * FROM rolling_team_stats", conn)
    teams = pd.read_sql_query("SELECT * FROM teams", conn)
    conn.close()

    data = []

    for _, game in games.iterrows():
        home_id = game['home_team_id']
        away_id = game['away_team_id']
        week = game['week']
        season = game['season']
        gid = game['game_id']

        # Get rolling stats for each team for that week
        home_stats = stats[(stats['team_id'] == home_id) & (stats['season'] == season) & (stats['week'] == week)]
        away_stats = stats[(stats['team_id'] == away_id) & (stats['season'] == season) & (stats['week'] == week)]

        if home_stats.empty or away_stats.empty:
            continue

        home = home_stats.iloc[0]
        away = away_stats.iloc[0]

        # Winner: 1 if home team wins
        winner = 1 if game['score_home'] > game['score_away'] else 0

        row = {
            'season': season,
            'week': week,
            'game_id': gid,
            'winner': winner,
            # Home team stats (offense & defense)
            'home_rolling_points_scored': home['rolling_points_scored'],
            'home_rolling_points_allowed': home['rolling_points_allowed'],
            'home_rolling_total_yards_for': home['rolling_total_yards_for'],
            'home_rolling_total_yards_against': home['rolling_total_yards_against'],
            'home_elo': home['rolling_elo'],
            # Away team stats (offense & defense)
            'away_rolling_points_scored': away['rolling_points_scored'],
            'away_rolling_points_allowed': away['rolling_points_allowed'],
            'away_rolling_total_yards_for': away['rolling_total_yards_for'],
            'away_rolling_total_yards_against': away['rolling_total_yards_against'],
            'away_elo': away['rolling_elo']
        }

        data.append(row)

    return pd.DataFrame(data)

def analyze_feature_importance(features_df):
    results = []

    # Point-Biserial Correlation (binary target vs. continuous features)
    for col in features_df.columns:
        if col in ['season', 'week', 'game_id', 'winner']:
            continue
        corr, pval = pointbiserialr(features_df['winner'], features_df[col])
        results.append({'feature': col, 'point_biserial': corr, 'p_value': pval})

    corr_df = pd.DataFrame(results).sort_values(by='point_biserial', key=abs, ascending=False)
    print("\n Point-Biserial Correlation Results:")
    print(corr_df[['feature', 'point_biserial', 'p_value']].to_string(index=False))

    # Logistic Regression Feature Weights
    X = features_df.drop(columns=['season', 'week', 'game_id', 'winner'])
    y = features_df['winner']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)

    coef_df = pd.DataFrame({
        'feature': X.columns,
        'logit_weight': model.coef_[0]
    }).sort_values(by='logit_weight', key=abs, ascending=False)

    print("\n Logistic Regression Coefficients:")
    print(coef_df.to_string(index=False))

    # Merge for summary if desired
    summary = pd.merge(corr_df, coef_df, on='feature')
    return summary

# Run after building features_df
# from previous step: features_df = build_feature_matrix(...)

# Usage
features_df = build_feature_matrix("../db_management/cfb_stats.db")
importance_summary = analyze_feature_importance(features_df)
#print(features_df.head())
