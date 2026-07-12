import pandas as pd

df = pd.read_csv("../data/processed/player_matches_analysis/player_match_stats.csv")

nyland = df[df["player_name"] == "Kylian Mbappé"]

print(
    nyland[
        [
            "event_id",
            "opponent_team_name",
            "stat_minutesPlayed",
            "stat_rating",
            
        ]
    ]
)