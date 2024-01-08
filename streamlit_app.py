import pandas as pd
import plotly.express as px
import streamlit as st

N_SEASONS = 25
N_GAMES = 16 * 17 + 13
MIN_POINTS = 17
QUARTER_SECONDS = 15 * 60
GAME_SECONDS = 4 * QUARTER_SECONDS  # assume no OT for now
MIN_YEAR = 1999
MAX_YEAR = 2023
SUMMARY_COLS = [
    "game_id",
    "home_team",
    "away_team",
    "game_date",
    "week",
    "qtr",
    "desc",
    "time",
    "total_home_score",
    "total_away_score",
    "home_score",
    "away_score",
]
DEFICIT_MAX_COLOR = 35
DEFICIT_MIN_COLOR = -DEFICIT_MAX_COLOR

@st.cache_data
def get_comeback_data():
    return pd.read_csv("./data/comebacks.csv")


@st.cache_data
def get_scoring_summaries():
    return pd.read_csv("./data/scoring_summaries.csv")

@st.cache_data
def get_game_id_mapping(series):
    # game_ids are formatted {year}_{week}_{home_team}_{away_team}
    def reformat_id(row):
        year, week, home, away = row.split("_")
        return f"{year}, Week {week}, {home} vs. {away}"

    unique_games = series.drop_duplicates()
    game_info_str = unique_games.apply(reformat_id)
    return pd.Series(game_info_str.values, index=unique_games.values).to_dict(), pd.Series(unique_games.values, index=game_info_str.values).to_dict()

st.title("Historical Comebacks in the NFL, 1999-2023")
st.markdown("""
Do you ever watch a game and think, "Oh, there's no way we'll come back from this?" Do you start Googling "largest comebacks in NFL history" to data-mine for hope?
Just me? Okay, this is app is clearly for me, and maybe anyone who wants to know just how unprecedented of a comeback your team will have to make.

The plot shows all comebacks in the NFL by over 2 scores, plotted by the deficit experienced by the winning team (y-axis) and the latest time they experienced the
deficit (x-axis; *i.e.*, right before the winning team scored).
Multiple deficits may appear per game; if you recovered from being down by, say, 33, you probably recovered from being down by 29 later in the game
(apologies to Vikings fans for the example).

**Disclaimer:** This is a *draft*/fun side project. There may be unforeseen bugs or issues with the data.
""")

def get_comeback_level(rate):
    if rate > 16:
        return "Come on, we see these like, once a week."
    elif rate > 8:
        return "Yeah, could happen."
    elif rate > 4:
        return "There's a few every season..."
    elif rate > 2:
        return "There's a *very* few every season..."
    elif rate > 1:
        return "There's like, one or two every season."
    elif rate > 0.5:
        return "Maybe next season..."
    elif rate > 0.2:
        return "If successful, this game will get its own Wikipedia page."
    elif rate > 0:
        return "Might as well get some lottery tickets..."
    else:
        return "UNPRECEDENTED!"

def get_game_time_str(game_time):
    if game_time >= GAME_SECONDS:
        return "End Reg."
    q = game_time // QUARTER_SECONDS + 1
    q_sec_remain = QUARTER_SECONDS - game_time % QUARTER_SECONDS
    min_remain = q_sec_remain // 60
    sec_remain = q_sec_remain % 60
    return f"Q{q} {min_remain}:{sec_remain:02}"

@st.cache_data
def get_hovertemplate():
    hover_lines = [
        '%{customdata[3]} (Week %{customdata[4]})',
        '%{customdata[7]} def. %{customdata[8]} %{customdata[9]}-%{customdata[10]}',
        'Overcame %{y}-point deficit (%{customdata[5]}-%{customdata[6]}, Q%{customdata[1]} %{customdata[2]})',
        'Win probability: %{customdata[11]:.2%}'
    ]
    return '<br>'.join(hover_lines)

@st.cache_data
def get_color(key):
    colorby_dict = {
        "Deficit": {"color": "max_future_deficit", "color_continuous_scale": "reds"},
        "Win probability": {"color": "score_team_wp_at_deficit", "color_continuous_scale": "blues"}
    }
    return colorby_dict[key]

@st.cache_data
def create_summary(df):
    first = df.iloc[0]
    winning_score = max(first["home_score"], first["away_score"])
    losing_score = min(first["home_score"], first["away_score"])
    winning_team = "total_home_score" if df["total_home_score"].iloc[-1] == winning_score else "total_away_score"
    losing_team = "total_away_score" if df["total_home_score"].iloc[-1] == winning_score else "total_home_score"
    return pd.DataFrame({
        "Time": "Q" + df["qtr"].astype(str) + " " + df["time"],
        "Play description": df["desc"].str.wrap(30),
        df["home_team"].iloc[0]: df["total_home_score"],
        df["away_team"].iloc[0]: df["total_away_score"],
        "Winner deficit": df[losing_team] - df[winning_team]
    })

@st.cache_data
def get_summary_header(df):
    df = df.iloc[0]
    winning_score = max(df["home_score"], df["away_score"])
    losing_score = min(df["home_score"], df["away_score"])
    winning_team = df["home_team"] if winning_score == df["home_score"] else df["away_team"]
    losing_team = df["away_team"] if winning_team == df["home_team"] else df["home_team"]
    return f"""
    #### Scoring summary
    **{df["game_date"]} (Week {df["week"]}): {winning_team} def. {losing_team} {winning_score}-{losing_score}**
    """

df = get_comeback_data()
scoring_df = get_scoring_summaries()

st.divider()
st.markdown("### Plot settings")
include_postseason = st.checkbox("Include postseason games", value=True)
deficit = st.slider("Hope level (minimum comeback size)", min_value=MIN_POINTS, max_value=35)
game_time = st.slider("Clutch level (game time, seconds elapsed)", min_value=0, max_value=GAME_SECONDS)
st.markdown(f"Game clock: **{get_game_time_str(game_time)}**")

deficit_df = df[(df["max_future_deficit"] >= deficit) & (df["deficit_end_seconds"] >= game_time)]
if not include_postseason:
    deficit_df = deficit_df[deficit_df["season_type"] == "REG"]

n_games = len(deficit_df["game_id"].unique())
rate = n_games / N_SEASONS
st.markdown(f"**Comeback level:** {get_comeback_level(rate)} (**{rate}** comebacks/season)")

with st.expander("Advanced filters"):
    min_year, max_year = st.slider("Seasons", min_value=MIN_YEAR, max_value=MAX_YEAR, value=(MIN_YEAR, MAX_YEAR))
    max_wp = st.slider("Maximum win probability", min_value=0., max_value=0.3, value=0.3)
    deficit_df = deficit_df[(deficit_df["year"] >= min_year) & (deficit_df["year"] <= max_year) & (deficit_df["score_team_wp_at_deficit"] <= max_wp)]
    post_n_games = len(deficit_df["game_id"].unique())
    st.markdown(f"{post_n_games}/{n_games} games under consideration")

st.divider()
colorby = st.radio(
    "Plotting mode",
    ["Deficit", "Win probability"],
)

fig_dict = dict(
    x="deficit_end_seconds",
    y="max_future_deficit",
    custom_data=[
        "game_id",
        "deficit_end_qtr",
        "deficit_end",
        "game_date",
        "week",
        "deficit_posteam_score",
        "deficit_defteam_score",
        "winning_team",
        "losing_team",
        "winning_score",
        "losing_score",
        "score_team_wp_at_deficit",
    ],
)

fig = px.scatter(
    deficit_df,
    **get_color(colorby),
    **fig_dict,
)

fig.update_layout(
    title=f"NFL Comebacks by more than two scores ({MIN_POINTS}+ pts.), 1999-2023",
    xaxis_title="Game time",
    yaxis_title="Winning team maximum deficit",
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(0, GAME_SECONDS + 1, QUARTER_SECONDS // 3)),
        ticktext=['Q1 15:00', 'Q1 10:00', 'Q1 5:00', 'Q2 15:00', 'Q2 10:00', 'Q2 5:00', 'Q3 15:00', 'Q3 10:00', 'Q3 5:00', 'Q4 15:00', 'Q4 10:00', 'Q4 5:00', 'End. Reg']
    ),
    coloraxis_colorbar=dict(title=colorby),
)
fig.update_traces(hovertemplate=get_hovertemplate())
for i in range(QUARTER_SECONDS, GAME_SECONDS + 1, QUARTER_SECONDS):
    fig.add_vline(i, line_dash="dash", line_color="white")
fig.update_xaxes(
    range=(game_time, GAME_SECONDS),
    constrain='domain'
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("""### Comeback scoring summaries

*"What!? How'd [insert team name] come back?"* If that's how you reacted, check out the searchable drop-down below to find scoring summaries for each of the comebacks.

To facilitate search, game information is indexed in the following format:

`"[YEAR], Week [WEEK], [HOME_TEAM] vs. [AWAY_TEAM]".`
""")
game_mappings, reverse_map = get_game_id_mapping(df.loc[df["max_future_deficit"] >= MIN_POINTS, "game_id"])
game_id = st.selectbox(
    "Comebacks",
    game_mappings.values(),
    index=None,
    placeholder="Select a game...",
)
scoring_slice = scoring_df.loc[scoring_df["game_id"] == reverse_map.get(game_id, False), SUMMARY_COLS]

if game_id is not None:
    st.markdown(get_summary_header(scoring_slice))
    st.table(
        create_summary(scoring_slice).reset_index(drop=True)
        .style.background_gradient(
            axis=1,
            vmin=DEFICIT_MIN_COLOR,
            vmax=DEFICIT_MAX_COLOR,
            cmap="RdYlGn_r",
            subset="Winner deficit"
        )
    )

st.markdown("""
Please direct comments, feedback, or requests to `ctrenton 'at' umich 'dot' edu`.

**Data availability statement:** All data is publicly available via [nflverse](https://github.com/nflverse) on GitHub.

*Data last updated 1/7/2024.*
""")
