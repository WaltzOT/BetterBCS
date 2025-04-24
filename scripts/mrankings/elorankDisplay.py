import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def print_weekly_top10_and_plot_by_season(db_path):
    conn = sqlite3.connect(db_path)

    # Load data
    elo = pd.read_sql_query("""
        SELECT team_id, season, week, rolling_elo
        FROM rolling_team_stats
        WHERE rolling_elo IS NOT NULL
    """, conn)

    teams = pd.read_sql_query("SELECT * FROM teams", conn)
    conn.close()

    # Merge team names
    elo = elo.merge(teams, on='team_id', how='left')

    # Compute Elo deltas
    elo['elo_delta'] = elo.sort_values(['team_id', 'season', 'week']) \
                          .groupby(['team_id', 'season'])['rolling_elo'] \
                          .diff().fillna(0)

    # Print weekly top 10 for each season
    for (season, week), group in elo.groupby(['season', 'week']):
        top10 = group.sort_values(by='rolling_elo', ascending=False).head(10)
        print(f"\n Season {season} – Week {week} Top 10 Elo")
        print(top10[['team_name', 'rolling_elo', 'elo_delta']].round(1).to_string(index=False))

    # Plot top 10 Elo per season separately
    for season in sorted(elo['season'].unique()):
        season_weeks = elo[elo['season'] == season]['week'].unique()
        if season < 2009 or season != 2020:
            last_week = max(season_weeks) - 1
        else:
            last_week = max(season_weeks)

        final_top10 = elo[(elo['season'] == season) & (elo['week'] == last_week)]
        final_top10 = final_top10.sort_values(by='rolling_elo', ascending=False).head(10)
        top_teams = final_top10['team_name'].tolist()

        plt.figure(figsize=(10, 6))
        for team in top_teams:
            team_data = elo[(elo['season'] == season) & (elo['team_name'] == team)]
            plt.plot(team_data['week'], team_data['rolling_elo'], label=team)

        plt.title(f"Elo Ratings Over Time – Top 10 Teams (Season {season})")
        plt.xlabel("Week")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.legend(loc="best", fontsize="x-small")
        plt.tight_layout()
        plt.show()

# Run it
print_weekly_top10_and_plot_by_season("../db_management/cfb_stats.db")
