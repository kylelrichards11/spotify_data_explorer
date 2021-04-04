""" Script to make a weekly top 25 playlist """
from datetime import datetime, timedelta

import pandas as pd

from firebase import FireManager
from spotify import Spotify

def get_date_range():
    end = datetime.now() + timedelta(days=1)
    end = datetime(end.year, end.month, end.day)
    start = end - timedelta(days=7)
    time_str = "%Y-%m-%d %H:%M"
    return start.strftime(time_str), end.strftime(time_str)

def get_prev_week(fb):
    prev_week = fb.get_prev_week()["tracks"]
    df = pd.DataFrame(prev_week)
    df.index = df["timestamp"]
    df = df.drop(columns=["timestamp"])
    return df.sort_index()

def trim_to_week(df):
    start, end = get_date_range()
    return df.loc[start:end, :]

def set_prev_week(fb, df, stage=True):
    df["timestamp"] = df.index
    df_dict = df.to_dict(orient="records")
    fb.set_prev_week({"tracks": df_dict}, stage=stage)

def get_top(df, k=25):
    df = df.loc[:, ["track_id", "listen_time"]]
    df = df.groupby("track_id").agg({
        "listen_time": "sum",
        "track_id": "count"
    }).rename(
        columns={"track_id":"listen_count"}
    ).sort_values(
        by=["listen_count", "listen_time"],
        ascending=False
    )
    return df.head(k)    


if __name__ == "__main__":
    fb = FireManager()
    sp = Spotify()
    df = get_prev_week(fb)
    df = trim_to_week(df)
    set_prev_week(fb, df, stage=False)
    top = get_top(df, k=25).index.tolist()
    sp.set_week_playlist(top)
