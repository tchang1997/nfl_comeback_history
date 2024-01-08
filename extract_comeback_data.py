import os

import pandas as pd
from tqdm.auto import tqdm
tqdm.pandas()

GAMEINFO_COLS = ["home_team", "away_team", "game_date", "week", "season_type", "qtr", "desc", "time", "game_seconds_remaining", "wp", "def_wp"]
SCORE_COLS = ["total_home_score", "total_away_score", "home_score", "away_score", "posteam", "defteam", "posteam_score", "defteam_score", "posteam_score_post", "defteam_score_post"]
WIN_LOSE_COLS = ["winning_team", "losing_team", "winning_score", "losing_score"]
DEFICIT_COLS = ["deficit_end", "deficit_end_qtr", "deficit_posteam_score", "deficit_defteam_score"]
DEFICIT_SOURCE_COLS = ["time", "qtr", "posteam_score", "defteam_score"]

QUARTER_SECONDS = 15 * 60

def get_scoring_summaries(group):
    scoring_plays = group.loc[(group[["total_home_score", "total_away_score"]] - group[["total_home_score", "total_away_score"]].shift(1)).sum(axis=1) > 0]
    return scoring_plays

def get_best_comebacks(group):
    # filter down to scoring plays only
    scoring_plays = get_scoring_summaries(group)

    # get game result info
    winner_col = "total_home_score" if group["home_score"].iloc[0] > group["away_score"].iloc[0] else "total_away_score"
    loser_col = "total_away_score" if winner_col == "total_home_score" else "total_home_score"
    winning_team = "home_team" if group["home_score"].iloc[0] > group["away_score"].iloc[0] else "away_team"
    losing_team = "away_team" if winning_team == "home_team" else "home_team"

    # filter down to "worst deficits" only (scoring plays where the other team does not face any larger deficit in the future)
    scoring_plays.loc[:, "max_future_deficit"] = (scoring_plays[loser_col] - scoring_plays[winner_col])[::-1].cummax()[::-1]
    worst_deficits = scoring_plays[(scoring_plays["max_future_deficit"] - scoring_plays["max_future_deficit"].shift(1)).fillna(-0.01) < 0]
    worst_deficits.loc[:, "max_future_deficit"] = worst_deficits.loc[:, "max_future_deficit"].clip(0, None)

    # create deficit metadata
    worst_deficits.loc[:, DEFICIT_COLS] = worst_deficits.loc[:, DEFICIT_SOURCE_COLS].shift(-1).values
    remain_seconds = worst_deficits.loc[:, "deficit_end"].apply(lambda x: None if pd.isnull(x) else int(x.split(":")[0]) * 60 + int(x.split(":")[1]))
    worst_deficits.loc[:, "deficit_end_seconds"] = worst_deficits["deficit_end_qtr"] * QUARTER_SECONDS - remain_seconds
    worst_deficits.loc[:, "score_team_at_deficit"] = worst_deficits["posteam"].where(worst_deficits["posteam_score_post"] - worst_deficits["posteam_score"] > 0, worst_deficits["defteam"])  # team that reduced the worst deficit so far
    worst_deficits.loc[:, "score_team_wp_at_deficit"] = worst_deficits["wp"].where(worst_deficits["score_team_at_deficit"] == worst_deficits["posteam"], worst_deficits["def_wp"]).shift(-1)  # pre-scoring WP at worst deficit

    # get winner info (for tooltip)
    win_lose_source_cols = [winning_team, losing_team, winning_team.replace("team", "score"), losing_team.replace("team", "score")]
    worst_deficits.loc[:, WIN_LOSE_COLS] = worst_deficits.loc[:, win_lose_source_cols].values
    return worst_deficits

def main(data_path="./data", begin_year=1999, end_year=2023):
    dfs = []
    scoring_summaries = []
    print("Reading data from", begin_year, "to", end_year)
    for year in range(begin_year, end_year + 1):
        print("Processing", year, "play-by-play data...")
        data_file = os.path.join(data_path, f"play_by_play_{year}.csv.gz")
        df = pd.read_csv(data_file, low_memory=False)
        filtered_df = df.loc[df["home_score"] != df["away_score"], ["play_id", "game_id"] + GAMEINFO_COLS + SCORE_COLS]
        game_groups = filtered_df.groupby("game_id")
        comebacks = game_groups.progress_apply(get_best_comebacks).reset_index(drop=True)
        summary = filtered_df[filtered_df["game_id"].isin(comebacks["game_id"])] \
            .groupby("game_id") \
            .progress_apply(get_scoring_summaries) \
            .reset_index(drop=True)
        dfs.append(comebacks)
        scoring_summaries.append(summary)
    comeback_df = pd.concat(dfs, keys=list(range(begin_year, end_year + 1)), names=["year"], axis=0)
    comeback_path = os.path.join(data_path, "comebacks.csv")
    comeback_df.to_csv(comeback_path)
    print("Saved comeback data to", comeback_path)

    scoring_df = pd.concat(scoring_summaries, keys=list(range(begin_year, end_year + 1)), names=["year"], axis=0)
    scoring_path = os.path.join(data_path, "scoring_summaries.csv")
    scoring_df.to_csv(scoring_path)
    print("Saved scoring summary data to", scoring_path)

if __name__ == '__main__':
    main()
