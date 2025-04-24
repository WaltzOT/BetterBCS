# BetterBCS

BetterBCS/
│
├── data/
│   └── cfb_box-scores_2002-2024.xlsx  # Your input data file
│
├── scripts/
│   ├── db_management/         
|   |   ├── createDB.py       # Creates SQLite database and tables
|   |   ├── fillDB.py         # Populates teams, games, and team stats
|   |   └── testDB.py
│   ├── model_training/
|   |   └── [model training scripts location]
│
├── models/
│   └── [optional trained models or priors if saved]
│
├── README.md
├── requirements.txt
└── .gitignore
