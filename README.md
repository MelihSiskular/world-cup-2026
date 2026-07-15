# ⚽ FIFA World Cup 2026 Analytics

A comprehensive data analytics project built around the 2026 FIFA World Cup using player-level and goal-level statistics collected from SofaScore.

The project focuses on these main areas:

-  Goal Analysis
-  Player Performance Analysis
-  Player Similarity Engine
-  Player Archetypes 

---

## Project Overview

This project collects and processes World Cup match data to create analytical datasets, rankings, visualizations, and team-of-the-week selections.

The goal is to transform raw football match events into meaningful insights about following topics.

---

# 1 - Goal Analysis

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

# 2 - Player Performance Analysis

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

The following example the best line-up for 4-3-3 formation in first group match
![](docs/images/01_Grup_1_Maçları_4-3-3.png)
---

# 3 - Player Similarity Engine

### Player Profile

| Player | Team | Position | Age | Minutes | Rating | Market Value |
|---|---|---|---:|---:|---:|---:|
| Michael Olise | France | M | 24.6 | 488 | 7.57 | EUR 144.0M |

This report identifies statistically similar players within the same broad
position group. The model uses position-specific, reliability-adjusted per-90
features, StandardScaler and cosine similarity.

### Example

```python

python -m src.player_similarity.breakdown.create_similarity_report \

    --player "Michael Olise"
```


### Closest Players

| Rank | Player | Team | Age | Minutes | Rating | Market Value | Similarity |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Florian Wirtz | Germany | 23.2 | 363 | 7.68 | EUR 95.0M | 86.55% |
| 2 | Sadio Mané | Senegal | 34.3 | 364 | 6.90 | EUR 5.6M | 69.09% |
| 3 | Andreas Schjelderup | Norway | 22.1 | 251 | 7.37 | EUR 31.0M | 68.79% |
| 4 | Nicolás González | Argentina | 28.3 | 182 | 6.87 | EUR 23.0M | 67.50% |
| 5 | Lamine Yamal | Spain | 19.0 | 405 | 7.25 | EUR 215.0M | 64.76% |
| 6 | Martin Ødegaard | Norway | 27.6 | 471 | 6.93 | EUR 71.0M | 63.68% |
| 7 | Johan Manzambi | Switzerland | 20.7 | 200 | 7.77 | EUR 54.0M | 63.35% |
| 8 | Mohamed Salah | Egypt | 34.1 | 428 | 7.24 | EUR 21.0M | 60.36% |
| 9 | Bruno Guimarães | Brazil | 28.7 | 419 | 7.15 | EUR 72.0M | 60.35% |
| 10 | Brahim Díaz | Morocco | 26.9 | 462 | 6.85 | EUR 37.0M | 59.94% |

### Quick Summary

- **Most similar player:** Florian Wirtz
- **Highest overall similarity:** 86.55%
- **Strongest matching areas:** Overall Quality (100.0%), Carrying & Dribbling (97.1%), Creativity (93.5%)
- **Candidate list size:** 10
- **Minimum similarity included:** 20.0%

## Detailed One-to-One Comparisons
![](docs/images/player_similarity/scout_reports/michael_olise_vs_florian_wirtz_scout_report.png)
---

# 4 - Player Archetypes

Players are automatically grouped into football-specific archetypes using unsupervised machine learning.

Different position groups are clustered independently:

- Goalkeepers
- Defenders
- Midfielders
- Forwards

### Examples:

Player | Team | Position | Archetype | Key Strengths |
|---|---|---|---|---|
| Michael Olise | France | M | Wide Creator | Creativity, Progression, Dribbling |
| Florian Wirtz | Germany | M | Wide Creator | Creativity, Passing, Progression |
| Rodri | Spain | M | Tempo Controller | Passing Volume, Progression, Ball Security |
| Leandro Paredes | Argentina | M | Tempo Controller | Progression, Passing Volume, Ball Security |
| Jude Bellingham | England | M | Goal-Threat Midfielder | Scoring Threat, Dribbling, Creativity |
| Declan Rice | England | M | Ball-Winning Midfielder | Defensive Work, Duels, Recoveries |
| Pau Cubarsí | Spain | D | Ball-Carrying Defender | Progression, Passing, Ball Carrying |
| Nuno Mendes | Portugal | D | Attacking Full-Back | Wide Attack, Progression, Crossing |
| Thibaut Courtois | Belgium | G | Commanding Goalkeeper | Box Command, Long Distribution, Sweeping |
| Kylian Mbappé | France | F | Poacher - Shooting Volume | Finishing, Shooting Volume, Dribbling |

### Example Player Query

```bash
python -m src.player_archetypes.show_player \
  --player "Michael Olise"
```

```text
Player:        Michael Olise
Team:          France
Position:      M
Archetype:     Wide Creator
Cluster Size:  29

Top Archetype Strengths:
- Creativity
- Progression
- Wide Creation
- Dribbling

Closest Members:
1. Florian Wirtz
2. Sadio Mané
3. Andreas Schjelderup
4. Nicolás González
5. Martin Ødegaard
```

### Examples - Archtype Map
![](docs/images/player_archetypes/forward_archetype_map.png)

Each point represents one player. Players positioned close to each other have
similar statistical role profiles. The `X` markers represent archetype centers.

> Archetypes describe tournament-based statistical production. They should not
> be interpreted as definitive tactical roles without positional tracking,
> touch maps and longer-term performance data.




## Generated Datasets

### Goal Analysis

- `world_cup_2026_goals_sofascore.csv` 
- `team_goal_buckets.csv`

### Player Performance

- `matches.csv`
- `player_match_stats.csv`
- `top_players_by_stage_position.csv`
- `teams_by_formation.csv`

### Player Similartiy
- `player_similarity_breakdown_long.csv`

### Player Archetypes
- `archetype_summary.csv`
- `player_archetypes.csv`
---

## Technologies

- Python
- Pandas
- Playwright
- Matplotlib
- Pillow
- Numpy
- Scikit-Learn
- Cosine Similarity
- K-Means Clustering
- PCA


---

## Project Structure

```text
src/
├── goal_minute/
├── player_archetypes/
├── player_similarity/
├── players/

data/
└── processed/

docs/
└── images/
```

---

## Sample Insights

Examples of questions that can be answered using this project:

- Which minute ranges produced the highest number of goals?
- How would a Team of the Week look in different formations?- Which defenders performed best during the group stage?
- Who are the closest alternatives to well known players?
- Which players have the most unique statistical profiles?
---


## Data Source

Match events and player statistics are collected from SofaScore and transformed into analytical datasets for educational and research purposes.

---

## Author

- Melih Şişkular