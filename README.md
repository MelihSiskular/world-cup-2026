# ⚽ FIFA World Cup 2026 Analytics

A data analytics project built around the 2026 FIFA World Cup using player-level and goal-level statistics collected from SofaScore.

The project focuses on two main areas:

-  Goal Analysis
-  Player Performance Analysis

---

## Project Overview

This project collects and processes World Cup match data to create analytical datasets, rankings, visualizations, and team-of-the-week selections.

The goal is to transform raw football match events into meaningful insights about:

- Goal scoring patterns
- Team scoring behavior
- Individual player performances
- Position-based rankings
- Team of the Week selections
- Formation visualizations

---

## Goal Analysis

Goal-related datasets are used to analyze:

- Goal timing distributions
- Team scoring tendencies
- Late-game goal patterns
- Goal bucket analysis
- Tournament-wide scoring trends

### Example
![](docs/images/goal_minute/team_goal_buckets_chart.png)

### Example
![](docs/images/goal_minute/goal_minute_distribution_chart.png)

---

## Player Performance Analysis

Player-level match statistics are used to evaluate:

- Match ratings
- Position-specific performance
- Stage-based rankings
- Team of the Week selections
- Formation comparisons

### Example
The following example filters the highest-rated forwards from the first group-stage matchday.

```python
import pandas as pd

# Available in data folder
df = pd.read_csv(
    "data/processed/weekly_team_analysis/"
    "top_players_by_stage_position.csv"
)

# Top 10 Forward Players 
top_forwards = df[
    (df["round_number"] == 1)
    & (df["analysis_position"] == "F")
].head(10)

print(
    top_forwards[
        [
            "position_rank",
            "player_name",
            "national_team_name",
            "opponent_team_name",
            "stat_minutesPlayed",
            "stat_rating",
        ]
    ]
)
```
### Sample Output
| Rank | Player | Team | Opponent | Minutes | Rating |
|---:|---|---|---|---:|---:|
| 1 | Lionel Messi | Argentina | Algeria | 80 | 10.0 |
| 2 | Folarin Balogun | USA | Paraguay | 72 | 9.0 |
| 3 | Alexander Isak | Sweden | Tunisia | 89 | 8.6 |
| 4 | Kai Havertz | Germany | Curaçao | 90 | 8.4 |
| 5 | Luis Díaz | Colombia | Uzbekistan | 89 | 8.2 |
| 6 | Crysencio Summerville | Netherlands | Japan | 70 | 8.1 |
| 7 | Amad Diallo | Côte d'Ivoire | Ecuador | 34 | 8.0 |
| 8 | Deniz Undav | Germany | Curaçao | 26 | 7.9 |
| 9 | Harry Kane | England | Croatia | 90 | 7.8 |
| 10 | Kang-in Lee | South Korea | Czechia | 90 | 7.7 |

### Example
The best line-up for 4-3-3 formation in first week
![](docs/images/formation_visuals_v3/individual/01_Grup_1_Maçları_4-3-3.png)
---

## Generated Datasets

### Goal Analysis

- `world_cup_2026_goals_sofascore.csv` 
- `team_goal_buckets.csv`

### Player Performance

- `matches.csv`
- `player_match_stats.csv`
- `top_players_by_stage_position.csv`
- `teams_by_formation.csv`

---

## Technologies

- Python
- Pandas
- Playwright
- Matplotlib
- Pillow

---

## Project Structure

```text
src/
├── goal_minute/
├── players/

data/
└── processed/

docs/
└── images/
```

---

## Sample Insights

Examples of questions that can be answered using this project:

- Which teams score the most goals?
- Which minute ranges produce the most goals?
- Which defenders performed best during the group stage?
- How would a Team of the Week look in a 4-3-3 formation?
- Which players consistently achieved the highest ratings?

---

## Future Improvements
- Tournament prediction models
- Player similarity analysis
- Team strength ratings
- Interactive dashboards

---

## Disclaimer

This project was created for educational and portfolio purposes.

---

## AUTHOR

- Melih Şişkular