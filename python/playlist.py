""" Script to make a weekly top 25 playlist """
from datetime import datetime, timedelta

import pandas as pd
import pytz

from firebase import FireManager
from prefect import Flow, task
from prefect.schedules import IntervalSchedule
from spotify import Spotify


## FUNCTIONS
def get_prev_week_dates():
    """ Gets the start and end dates for the previous week.
    
    The start date is 7 days before the current time. The end date is the 
    current time.

    Arguments
    ---------
    None

    Returns
    -------
    A tuple of strings whose first element is the start date and whose second
    element is the end date.
    """
    end = datetime.now() + timedelta(days=1)
    end = datetime(end.year, end.month, end.day)
    start = end - timedelta(days=7)
    time_str = "%Y-%m-%d %H:%M"
    return start.strftime(time_str), end.strftime(time_str)


# TASKS
@task(max_retries=10, retry_delay=timedelta(seconds=600))
def get_prev_week_tracks_task(fb):
    """ Gets all of the tracks played in the previous week.
    
    These tracks are stored in a specific document in Firestore and the Firebase
    class has a method to easily retrieve them. This function also converts the 
    index to the timestamp of each track and sorts the tracks by time.
    
    Arguments
    ---------
    fb (Firebase Object): An instance of the Firebase class

    Returns
    -------
    DataFrame: A dataframe of all of the tracks played in the previous week.
    """
    prev_week = fb.get_prev_week()["tracks"]
    df = pd.DataFrame(prev_week)
    df.index = df["timestamp"]
    df = df.drop(columns=["timestamp"])
    return df.sort_index()


@task
def trim_to_week_task(df):
    """ Selects only the rows of the given dataframe that fall within the 
    previous week.

    Assumes the dataframe's index is a DatetimeIndex

    Arguments
    ---------
    df (DataFrame): The dataframe to trim

    Returns
    -------
    (DataFrame): The trimmed dataframe.
    """
    start, end = get_prev_week_dates()
    return df.loc[start:end, :]


@task(max_retries=10, retry_delay=timedelta(seconds=600))
def update_prev_week_task(fb, df, stage=True):
    """ Sets the previous week document in firebase to only include listens that
    are still from the previous week.
    
    The previous week document in Firestore has no way to enforce that its 
    listens are actually only from the previous week. All listens that are 
    listened to are added to this document. If left unpruned, eventually the 
    document would become too large. This function updates the document by 
    resetting it and then only adding back listens that are still less than a 
    week from being played.

    Arguments
    ---------
    fb (Firebase Object): An instance of the firebase class

    df (pd.DataFrame): A dataframe of listens that are from the previous week

    stage (boolean, default=True): Whether or not to write to the stage version
    of the prev week doc. If false, then the production version is written to.

    Returns
    -------
    None
    """
    df["timestamp"] = df.index
    df_dict = df.to_dict(orient="records")
    fb.set_prev_week({"tracks": df_dict}, stage=stage)


@task(max_retries=10, retry_delay=timedelta(seconds=600))
def set_week_playlist_task(sp, top_ids):
    """ Sets the playlist in spotify to the given tracks in top_ids.
    
    Arguments
    ---------
    sp (Spotipy Object): An instance of the Spoitipy class.
    
    top_ids (list): A list of track ids to add to the playlist. The order of the
    list is the order the tracks will be in the playlist.
    """
    sp.set_week_playlist(top_ids)


@task
def get_top_tracks_task(df, k=25):
    """ Aggregates and sorts tracks to determine the most listened to.
    
    Arguments
    ---------
    df (pd.DataFrame): A dataframe of listens from the prev week document in 
    Firestore
    
    k (int, default=25): How many tracks to return

    Returns
    -------
    (list): A list of the top k tracks' ids in order.
    """
    df = df.loc[:, ["track_id", "listen_time"]]
    df = df.groupby("track_id").agg({
        "listen_time": "sum",
        "track_id": "count"
    }).rename(columns={
        "track_id": "listen_count"
    }).sort_values(by=["listen_count", "listen_time"], ascending=False)
    return df.head(k).index.tolist()


# FLOWS
def build_update_playlist_flow(name):
    """ A flow to update the weekly top 25 playlist. This flow should run
    preiodically, at minimum once a day.
    """
    fb = FireManager()
    sp = Spotify()
    schedule = IntervalSchedule(
        start_date = datetime(2021, 4, 26, 7, 0, 0, 0, pytz.UTC),
        interval = timedelta(hours=24),
    )
    with Flow(name, schedule=schedule) as flow:
        df = get_prev_week_tracks_task(fb)
        df = trim_to_week_task(df)
        update_prev_week_task(fb, df, stage=True)
        top = get_top_tracks_task(df, k=25)
        set_week_playlist_task(sp, top)
    return flow


if __name__ == "__main__":
    flow = build_update_playlist_flow("Update Playlist")
    flow.run()
