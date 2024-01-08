import pandas as pd

from drive_viewer.constants.football import DOWNS
from drive_viewer.constants.text import WRAPPER

def get_drive_title(drive_df):
    drive_series = drive_df.iloc[0]
    team = drive_series["posteam"]
    drive = drive_series["drive"]
    qtr = drive_series["qtr"]
    time = drive_series["time"]
    return f"<b>Drive #{int(drive)}:</b> {team}, Q{qtr} {time}"

def get_down_info(drive_df):

    def get_down_tooltip(row):
        down = row["down"]
        if pd.isnull(down):
            play_type = row["play_type"]
            return f"<b>{play_type}</b>"
        togo = row["ydstogo"]
        yrdln = row["yrdln"]
        down_ord = DOWNS[int(down) - 1]
        return f"<b>{yrdln}: {down_ord} & {togo} </b>"
    return drive_df.apply(get_down_tooltip, axis=1)

def get_tooltip_text(drive_df):

    def get_tooltip_for_play(row):
        play_desc = WRAPPER.fill(row["desc"]).replace('\n', '<br>')
        start = row["yrdln"]
        end = row["end_yard_line"]

        qtr = row["qtr"]
        start_time = row["time"]
        end_time = row["end_clock_time"]
        gain = row["yards_gained"]
        posteam_type = row["posteam_type"]
        play_type = row["play_type"]

        if play_type == "no_play":
            return f"<b>(Q{qtr} {start_time}) {start}</b><br>{play_desc}"

        home_team = row["posteam"] if posteam_type == "home" else row["defteam"]
        away_team = row["posteam"] if posteam_type != "home" else row["defteam"]

        if pd.notnull(gain):
            gain_str = f"{int(gain):+}"
            if pd.isnull(end):
                end = numeric_to_yrdln(
                    yrdln_to_numeric(
                        row["yrdln"],
                        home_team
                    ) + (2 * (posteam_type == "home") - 1) * int(gain),
                    home_team,
                    away_team)
        else:
            gain_str = "N/A"
            return f"<b>(Q{qtr} {start_time}) {start}<br>{play_desc}"

        return f"<b>(Q{qtr} {start_time}) {start}  ➤ {end} [{gain_str} yds]</b><br>Play selection: {play_type}<br>{play_desc}"

    return drive_df.apply(get_tooltip_for_play, axis=1)

def yrdln_to_numeric(row, home):
    # home team moves right, away team moves left
    side, num = row.split()
    if home == side:
        return int(num)
    else:
        return 100 - int(num)

def numeric_to_yrdln(num, home, away):
    if num < 50:
        return f"{home} {num}"
    elif num > 50:
        return f"{away} {100 - num}"
    else:
        return "50"
