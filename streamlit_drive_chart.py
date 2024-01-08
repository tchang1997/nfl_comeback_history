import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from drive_viewer.constants.columns import GAME_COLS, PLAY_COLS
from drive_viewer.constants.dimensions import DRAW_SCALE, DRIVE_PADDING, PLAY_HEIGHT, TEXT_MARGIN, X_HOME_10YD, X_AWAY_GOAL_LINE, X_NUMBER_SPACING
from drive_viewer.constants.football import FIELD_COLOR, PLAY_DICT, PLAY_MARKERS
from drive_viewer.annotate_utils import get_drive_title, get_down_info, get_tooltip_text, yrdln_to_numeric
from drive_viewer.draw_utils import add_end_zone_text, draw_numbers, fill_end_zone

OFFSET = 10

@st.cache_data
def get_game_df(week_df, game_id):
    game_df = week_df.loc[week_df["game_id"] == game_id, GAME_COLS + PLAY_COLS].dropna(
        subset=["drive", "play_type"]
    )
    game_df.loc[:, "yrdln"] = game_df.loc[:, "yrdln"].bfill()
    return game_df

@st.cache_data
def get_season_df(season):
    df = pd.read_csv(f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz")
    return df

def get_play_starts(drive_df, drive_index, home_team):
    play_start_series = drive_df["yrdln"].apply(yrdln_to_numeric, home=home_team) + OFFSET
    return play_start_series, go.Scatter(
        x=play_start_series,
        y=drive_index,
        mode="markers+text",
        marker=dict(color="orange"),
        hoverinfo="skip",
        text=get_down_info(drive_df),
        textposition="bottom center",
        textfont_size=14,
    )

def get_play_ends(drive_df, drive_index, home_team):
    penalty_idx = drive_df["penalty"].fillna(0).astype(int).tolist()
    touchdown_idx = drive_df["touchdown"].fillna(0).astype(int).tolist()

    play_direction_sign = 2 * (drive_df["posteam_type"] == "home") - 1
    play_end_series = drive_df["yrdln"].apply(yrdln_to_numeric, home=home_team) + play_direction_sign * drive_df["yards_gained"] + OFFSET
    play_text = drive_df["play_type"].map(PLAY_DICT).tolist()
    play_text = [str(msg) + "".join([emoji_suffix if drive_df[col].iloc[i] != 0 else "" for col, emoji_suffix in PLAY_MARKERS.items()]) for i, msg in enumerate(play_text)]
    play_ends = go.Scatter(
        x=play_end_series,
        y=drive_index,
        mode="markers+text",
        marker=dict(color="blue"),
        hovertext=get_tooltip_text(drive_df),
        showlegend=False,
        hoverinfo="text",
        text=play_text,
        textposition="top center",
        textfont_size=20,
    )
    return play_end_series, play_ends

def get_lines(drive_df, play_start_series, play_end_series, drive_index):
    return [
        dict(
            type="line",
            x0=play_start_series.iloc[i],
            y0=drive_index[i],
            x1=play_end_series.iloc[i],
            y1=drive_index[i],
            line=dict(
                color="black",
                width=2 if drive_df["play_type"].iloc[i] != "no_play" else 0,
                dash="dash",
            ),
        )
        for i in range(len(drive_df))
    ] + [
        dict(
            type="line",
            x0=x,
            y0=drive_index[0] + DRIVE_PADDING,
            x1=x,
            y1=drive_index[-1],
            line=dict(
                color="white",
                width=1,
            ),
        )
        for x in np.arange(X_HOME_10YD, X_AWAY_GOAL_LINE, X_NUMBER_SPACING)
    ]

def create_drive_chart(drive_no, game_df):

    drive_df = game_df.loc[game_df["drive"] == drive_no, PLAY_COLS]
    drive_index = PLAY_HEIGHT * np.arange(len(drive_df), -1, -1) + PLAY_HEIGHT

    home_team = game_df["home_team"].iloc[0]
    away_team = game_df["away_team"].iloc[0]
    posteam = drive_df["posteam"].iloc[0]
    posteam_type = drive_df["posteam_type"].iloc[0]
    side_of_field = drive_df["side_of_field"].iloc[0]

    play_start_series, play_starts = get_play_starts(drive_df, drive_index, home_team)
    play_end_series, play_ends = get_play_ends(drive_df, drive_index, home_team)

    data = [draw_numbers(drive_index[-1] + TEXT_MARGIN), draw_numbers(drive_index[0] + DRIVE_PADDING / 2 - TEXT_MARGIN)] + fill_end_zone(
        home_team,
        away_team,
        [drive_index[-1], drive_index[0] + DRIVE_PADDING / 2],
    ) + [play_starts, play_ends]
    lines = get_lines(drive_df, play_start_series, play_end_series, drive_index)
    layout = go.Layout(
        autosize=False,
        width=120 * DRAW_SCALE,
        height=max(6, len(drive_index)) * PLAY_HEIGHT * DRAW_SCALE,
        xaxis1=dict(range=[0, 120], autorange=False, tickmode='array', tickvals=np.arange(10, 111, 5).tolist(), showticklabels=False, fixedrange=True),
        yaxis1=dict(range=[drive_index[-1], drive_index[0] + DRIVE_PADDING / 2], showticklabels=False, showgrid=False, fixedrange=True),
        plot_bgcolor=FIELD_COLOR,
        shapes=lines,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Helvetica",
            font_color="black",
        )
    )
    fig = go.Figure(data, layout=layout)
    add_end_zone_text(fig, home_team, away_team, max((drive_index[0] + drive_index[-1] + DRIVE_PADDING * 0.75) / 2, 2 * PLAY_HEIGHT))
    fig.update_traces(
        marker=dict(
            size=12,
            line=dict(width=2, color='DarkSlateGrey')
        )
    )
    return drive_df, fig

st.markdown("# NFL Play-by-Play Drive Chart Visualizer")
st.markdown("""
    **Disclaimer:** This drive chart visualizer is *draft*/fun side project. There may be unforeseen bugs or issues with the data.
    This web app change without notice; nor is there any guarantee that it will be maintained.
""")
season = st.selectbox("Season", range(1999, 2024), index=None, placeholder="Select a season...",)

if season is not None:
    season_df = get_season_df(season)
    week = st.selectbox("Week", season_df["week"].unique(), index=None, placeholder="Select a week...")
    if week is not None:
        week_df = season_df.loc[season_df["week"] == week]
        game_id = st.selectbox("Game ID", week_df["game_id"].unique(), index=None, placeholder="Select a game...")
        if game_id is not None:
            game_df = get_game_df(week_df, game_id)
            _, _, hteam, ateam = game_id.split("_")
            st.markdown("""
            **Legend:**
            *There will one day be a legend here when the symbols are more finalized.*
            """)
            st.markdown(f"## Play-by-play visualization: {hteam} vs. {ateam} ({season}, Week {week})")
            st.markdown("""
            For best results, view in fullscreen.

            """)
            drive_groups = game_df.groupby("drive")
            posteams = drive_groups["posteam"].first().tolist()
            qtrs = drive_groups["qtr"].first().tolist()
            times = drive_groups["time"].first().tolist()
            start_times = [f"(Q{qtr} {time})" for qtr, time in zip(qtrs, times)]
            drive_arr = [f"{time} Drive {i} ({posteam})" for i, posteam, time in zip(range(1, len(game_df["drive"].unique()) + 1), posteams, start_times)]
            drive_id = st.selectbox("Drive", drive_arr)

            drive_df, fig = create_drive_chart(drive_arr.index(drive_id) + 1, game_df)
            st.plotly_chart(fig, use_container_width=True)
            st.divider()
            with st.expander("View raw play-by-play data"):
                st.write(drive_df)

st.divider()
st.markdown("""
Please direct comments, feedback, or requests to `ctrenton 'at' umich 'dot' edu`.

**Data availability statement:** All data is publicly available via [nflverse](https://github.com/nflverse) on GitHub.

*Data last updated 1/7/2024.*
""")
