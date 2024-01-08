import numpy as np
import plotly.graph_objects as go

from drive_viewer.constants.dimensions import (
    X_HOME_ENDZONE,
    X_AWAY_GOAL_LINE,
    X_HOME_10YD,
    X_NUMBER_SPACING,
    X_N_NUMBERS,
    YARD_NUMBERS,
)
from drive_viewer.constants.football import TEAM_COLORS, TEAM_NAMES

def draw_numbers(y):
    return go.Scatter(
        x=np.arange(X_HOME_10YD, X_AWAY_GOAL_LINE, X_NUMBER_SPACING),
        y=[y] * X_N_NUMBERS,
        mode='text',
        text=YARD_NUMBERS,
        textfont_size=30,
        textfont_family="Courier New, monospace",
        textfont_color="white",
        showlegend=False,
        hoverinfo='none'
    )

def fill_end_zone(home, away, range_arr):
    data = []
    bot, top = range_arr
    for x_min in [X_HOME_ENDZONE, X_AWAY_GOAL_LINE]:
        data.append(
            go.Scatter(
                x=[x_min, x_min, x_min + 10, x_min + 10, x_min],
                y=[bot, top, top, bot, bot],
                fill="toself",
                fillcolor=TEAM_COLORS[home] if x_min == X_HOME_ENDZONE else TEAM_COLORS[away],
                mode="lines",
                line=dict(
                    color="white",
                    width=3
                ),
                opacity=1,
                showlegend=False,
                hoverinfo="skip"
            )
        )
    return data

def add_end_zone_text(fig, home, away, y):
    for x_min in [X_HOME_ENDZONE, X_AWAY_GOAL_LINE]:
        fig.add_annotation(
            x=x_min + 5,
            y=y,
            text=f"<b>{TEAM_NAMES[home if x_min == X_HOME_ENDZONE else away]}</b>",
            showarrow=False,
            font=dict(
                family="Helvetica, sans-serif",
                size=32,
                color="white",
            ),
            textangle=90 if x_min == X_HOME_ENDZONE else 270
        )
