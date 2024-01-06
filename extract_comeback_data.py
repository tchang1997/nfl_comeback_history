import os

import pandas as pd
from tqdm.auto import tqdm
tqdm.pandas()

GAMEINFO_COLS = ["home_team", "away_team", "game_date", "week", "season_type", "drive", "qtr", "down", "ydstogo", "yrdln", "desc", "time", "game_seconds_remaining"]
SCORE_COLS = ["total_home_score", "total_away_score", "home_score", "away_score"]
QUARTER_SECONDS = 15 * 60

def get_best_comebacks(group):
    scoring_plays = group.loc[(group[SCORE_COLS] - group[SCORE_COLS].shift(1)).sum(axis=1) > 0]
    winner_col = "total_home_score" if group["home_score"].iloc[0] > group["away_score"].iloc[0] else "total_away_score"
    loser_col = "total_away_score" if winner_col == "total_home_score" else "total_home_score"
    scoring_plays.loc[:, "max_future_deficit"] = (scoring_plays[loser_col] - scoring_plays[winner_col])[::-1].cummax()[::-1]
    worst_deficits = scoring_plays[(scoring_plays["max_future_deficit"] - scoring_plays["max_future_deficit"].shift(1)).fillna(-0.01) < 0]
    worst_deficits.loc[:, "max_future_deficit"] = worst_deficits.loc[:, "max_future_deficit"].clip(0, None)
    worst_deficits.loc[:, "deficit_end"] = worst_deficits["time"].shift(-1)
    worst_deficits.loc[:, "deficit_end_qtr"] = worst_deficits["qtr"].shift(-1)

    remain_seconds = worst_deficits.loc[:, "deficit_end"].apply(lambda x: None if pd.isnull(x) else int(x.split(":")[0]) * 60 + int(x.split(":")[1]))
    worst_deficits.loc[:, "deficit_end_seconds"] = (worst_deficits["deficit_end_qtr"] - 1) * 15 * 60 + 15 * 60 - remain_seconds
    return worst_deficits

def main(data_path="./data", begin_year=1999, end_year=2023):
    dfs = []
    print("Reading data from", begin_year, "to", end_year)
    for year in range(begin_year, end_year + 1):
        print("Processing", year, "play-by-play data...")
        data_file = os.path.join(data_path, f"play_by_play_{year}.csv.gz")
        df = pd.read_csv(data_file, low_memory=False)
        comebacks = df.loc[df["home_score"] != df["away_score"], ["play_id", "game_id"] + GAMEINFO_COLS + SCORE_COLS].groupby("game_id").progress_apply(get_best_comebacks)
        dfs.append(comebacks)
    comeback_df = pd.concat(dfs, keys=list(range(begin_year, end_year + 1)), names=["year"], axis=0)

    comeback_path = os.path.join(data_path, "comebacks.csv")
    comeback_df.to_csv(comeback_path)
    print("Saved comeback data to", comeback_path)
    return comeback_df

if __name__ == '__main__':
    main()
