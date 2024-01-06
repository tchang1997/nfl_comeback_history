import pandas as pd
import plotly.express as px
import streamlit as st

N_SEASONS = 25
N_GAMES = 16 * 17 + 13

@st.cache_data
def get_comeback_data():
    return pd.read_csv("./data/comebacks.csv")

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
    if game_time >= 3600: return "End Reg."
    q = game_time // 900 + 1
    q_sec_remain = 900 - game_time % 900
    min_remain = q_sec_remain // 60
    sec_remain = q_sec_remain % 60
    return f"Q{q} {min_remain}:{sec_remain:02}"

df = get_comeback_data()

include_postseason = st.checkbox("Include postseason games")
deficit = st.slider("Hope level (minimum comeback size)", min_value=17, max_value=35)
game_time = st.slider("Clutch level (game time)", min_value=0, max_value=3600)
st.markdown(f"Game time: {get_game_time_str(game_time)}")

deficit_df = df[(df["max_future_deficit"] >= deficit) & (df["deficit_end_seconds"] >= game_time)]
if not include_postseason:
    deficit_df = deficit_df[deficit_df["season_type"] == "REG"]

rate = len(deficit_df["game_id"].unique()) / N_SEASONS
st.markdown(f"**Comeback level:** {get_comeback_level(rate)}")
st.markdown(f"**{rate}** comebacks/season of this scale or greater")

fig = px.scatter(
    deficit_df,
    x="deficit_end_seconds",
    y="max_future_deficit",
    color="max_future_deficit",
    color_continuous_scale="reds",
    custom_data=["game_id", "deficit_end_qtr", "deficit_end"],
)

fig.update_layout(
    title="NFL Comebacks by more than two scores (17+ pts.), 1999-2023",
    xaxis_title="Game time",
    yaxis_title="Winning team maximum deficit",
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(0, 3601, 300)),
        ticktext=['Q1 15:00', 'Q1 10:00', 'Q1 5:00', 'Q2 15:00', 'Q2 10:00', 'Q2 5:00', 'Q3 15:00', 'Q3 10:00', 'Q3 5:00', 'Q4 15:00', 'Q4 10:00', 'Q4 5:00', 'End. Reg']
    )
)
fig.update_traces(hovertemplate='%{customdata[0]}<br>Overcame %{y}-point deficit (Q%{customdata[1]} %{customdata[2]})') #
for i in range(900, 3601, 900):
    fig.add_vline(i, line_dash="dash", line_color="white")
fig.update_xaxes(
    range=(game_time, 15 * 60 * 4 + 10 * 60),
    constrain='domain'
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("""
Please direct comments, feedback, or requests to `ctrenton 'at' umich 'dot' edu`.

**Data availability statement:** All data is publicly available via [nflverse](https://github.com/nflverse) on GitHub.

*Data last updated 1/5/2024.*
""")
