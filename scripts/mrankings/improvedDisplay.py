import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def print_weekly_top10_with_deltas(db_path):
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

    # Compute Elo delta
    elo = elo.sort_values(['team_id', 'season', 'week'])
    elo['elo_delta'] = elo.groupby(['team_id', 'season'])['rolling_elo'].diff().fillna(0)

    # Prepare final top 10 list across all weeks
    full_top10_list = []

    for (season, week), group in elo.groupby(['season', 'week']):
        # Sort by Elo descending, get top 10
        top10 = group.sort_values(by='rolling_elo', ascending=False).head(10).copy()

        # Assign proper rank values (1 to len(top10))
        top10 = top10.sort_values(by='rolling_elo', ascending=False).reset_index(drop=True)
        top10['rank'] = top10.index + 1

        full_top10_list.append(top10)

    top10_df = pd.concat(full_top10_list)
    top10_df = top10_df.sort_values(['team_id', 'season', 'week'])

    # Compute rank_delta
    top10_df['rank_delta'] = top10_df.groupby(['team_id', 'season'])['rank'].diff().fillna(0).astype(int)

    # Print week-by-week top 10s with deltas + dropped teams
    previous_week_top = {}

    for (season, week), group in top10_df.groupby(['season', 'week']):
        print(f"\n Season {season} – Week {week} Top 10 Elo")
        print(group.sort_values(by='rank')[['rank', 'team_name', 'rolling_elo', 'elo_delta', 'rank_delta']].round(1).to_string(index=False))

        # Dropped from top 10
        current_top_teams = set(group['team_name'])
        previous_top_teams = previous_week_top.get((season, week - 1), set())

        dropped = previous_top_teams - current_top_teams
        if dropped:
            print("  Teams that dropped out of the Top 10:", ", ".join(sorted(dropped)))

        # Save this week’s top 10 for next comparison
        previous_week_top[(season, week)] = current_top_teams

    # Plot separate Elo charts per season for end-of-season Top 10 teams
    for season in sorted(elo['season'].unique()):
        if season < 2009 or season == 2020:
            last_week = elo[elo['season'] == season]['week'].max()
        else:
            last_week = elo[elo['season'] == season]['week'].max() - 1
        final_top10 = elo[(elo['season'] == season) & (elo['week'] == last_week)]
        final_top10 = final_top10.sort_values(by='rolling_elo', ascending=False).head(10)

        plt.figure(figsize=(10, 6))
        for team in final_top10['team_name']:
            team_data = elo[(elo['season'] == season) & (elo['team_name'] == team)]
            plt.plot(team_data['week'], team_data['rolling_elo'], label=team)

        plt.title(f"Elo Ratings – Top 10 Final Teams (Season {season})")
        plt.xlabel("Week")
        plt.ylabel("Elo Rating")
        plt.grid(True)
        plt.legend(loc="best", fontsize="x-small")
        plt.tight_layout()
        plt.show()

# Run it
print_weekly_top10_with_deltas("../db_management/cfb_stats.db")
