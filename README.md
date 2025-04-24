# BetterBCS

BetterBCS is a personal project structured around creating another version of BCS rankings, and then ultimately working into creating an algorithm to track and predict headto head matchups week to week.

## File Structure
```
BetterBCS/
│
├── data/
│   └── cfb_box-scores_2002-2024.xlsx  # Your input data file
│
├── scripts/
│   ├── db_management/         
|   |   ├── createDB.py            # Creates SQLite database and tables
|   |   ├── fillDB.py              # Populates teams, games, and team stats
|   |   └── testDB.py              # Checks to make sure DBs are filled
│   ├── mrankings/         
|   |   ├── fillRanks.py           # Calculates average stats and fills out statistcal rankings
|   |   ├── fillElo.py             # Calculates elo off of stats and wins and losses, ulitizes strength of opponent with decay as well.
|   |   ├── rankCheck.py           # Test to make sure ranks are filled
|   |   ├── eloCheck2.py           # Checks to make sure elos are filled in
|   |   └── elorankDisplay.py      # Displays ranks over time includeing delta elo, then also creates graphs for top10 teams at end of season elo overtime
│   ├── model_training/
|   |   └── bayesian-trainModel.py # Online learning model with bayesian weights.
│
├── models/
│   └── [optional trained models or priors if saved]
│
├── README.md
├── requirements.txt
└── .gitignore
```
