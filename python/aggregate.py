import pandas as pd

import json
import re
from datetime import datetime, timezone

import pandas as pd
import numpy as np

from firebase import FireManager

df_dtypes = {
    'ts':str,
    'username':str,
    'platform':str,
    'ms_played':int,
    'conn_country':str,
    'user_agent_decrypted':str,
    'track_name':str,
    'artist_name':str,
    'album_name':str,
    'reason_start':str,
    'reason_end':str,
    'shuffle':bool,
    'skipped':bool,
    'offline':bool,
    'offline_timestamp':str,
    'incognito_mode':bool,
    'metro_code':str,
    'longitude':float,
    'latitude':float,
    'city':str,
    'region':str,
    'episode_name':str,
    'episode_show_name':str
}

def save_dict_json(my_dict, filename):
    with open(f"{filename}.json", "w") as f:
        f.write(json.dumps(my_dict))

def read_dict_json(filename):
    with open(f"{filename}.json", "r") as f:
        return json.load(f)

def read_bulk_tracks():
    f = open("../data/AllSongs.json", "r")
    rows = []
    for row in f:
        r = json.loads(row) 
        rows.append(r)
    f.close()
    rows.reverse()
    df = pd.DataFrame(rows)
    df = df.rename(columns={'master_metadata_track_name':'track_name', 'master_metadata_album_artist_name':'artist_name', 'ts':'end_time'})
    df = df.loc[:, ['track_name', 'artist_name', 'ms_played', 'end_time']]
    return df.dropna()

def read_2020_tracks():
    data = []
    for file_num in range(1, 4):
        with open(f"../data/2020_year_data/StreamingHistory{file_num}.json") as f:
            data.extend(json.load(f))
    df = pd.DataFrame(data)
    df = df.rename(columns={'trackName':'track_name', 'artistName':'artist_name', 'endTime':'end_time', 'msPlayed':'ms_played'})
    return df.dropna()

def write_df_dict(df, path):
    if type(df) == pd.Series:
        dict = df.to_dict()
    else:
        dict = df.to_dict(orient="records")
    json_str = json.dumps(dict)
    with open(path, 'w') as f:
        f.write(json_str)

def group(tracks_cleaned):
    plays = pd.Series(np.ones(tracks_cleaned.shape[0]).astype(int), name="play_count")
    tracks = pd.concat((tracks_cleaned, plays), axis=1)
    tracks = pd.get_dummies(tracks, columns=["year", "hour", "month", "year_month"])
    tracks_songs = tracks.drop(columns=["artist_name", "day", "minute", "play_id"])
    tracks_songs = tracks_songs.groupby('track_name').sum().astype(int)
    tracks_artists = tracks.drop(columns=["track_name", "day", "minute", "play_id"])
    tracks_artists = tracks_artists.groupby('artist_name').sum().astype(int)
    return tracks_songs, tracks_artists

def clean(df):
    df['track_name'] = df['track_name'].astype(str)
    df['artist_name'] = df['artist_name'].astype(str)
    df['ms_played'] = pd.to_numeric(df['ms_played'])
    df['end_time'] = df['end_time'].apply(lambda date : re.sub(r':[0-9][0-9] UTC', '', date))
    df['end_time'] = df['end_time'].apply(lambda date_str : datetime.strptime(date_str, '%Y-%m-%d %H:%M'))
    df['year'] = df['end_time'].apply(lambda dt : dt.date().year)
    df['month'] = df['end_time'].apply(lambda dt : dt.date().month)
    df['day'] = df['end_time'].apply(lambda dt : dt.date().day)
    df['weekday'] = df['end_time'].apply(lambda dt : dt.weekday())
    df['hour'] = df['end_time'].apply(lambda dt : dt.time().hour)
    df['minute'] = df['end_time'].apply(lambda dt : dt.time().minute)
    df['year_month'] = df.apply(lambda row : f"{row['year']}{0 if row['month'] < 10 else ''}{row['month']}", axis=1)
    df['timestamp'] = df['end_time'].apply(lambda dt : int(dt.timestamp()))
    df = df.sort_values(by='end_time').reset_index(drop=True)
    return df.drop(columns=['end_time'])  

def get_artist_songs(tracks):
    tracks = tracks.loc[:, ["artist_name", "track_name"]]
    tracks = tracks.drop_duplicates()
    tracks = tracks.groupby("artist_name")['track_name'].apply(list)
    return tracks

def get_info(ids):
    info = pd.read_json("tracks_info_final.json", orient="index", encoding="utf-8")
    bulk_tracks = read_bulk_tracks()
    year_tracks = read_2020_tracks()
    tracks = pd.concat((bulk_tracks, year_tracks))
    cleaned_tracks = clean(tracks)

    cleaned_tracks["track_id"] = cleaned_tracks.apply(lambda row : ids.loc[f"{row['track_name']} {row['artist_name']}", "track_id"], axis=1)
    cleaned_tracks = cleaned_tracks[cleaned_tracks["track_id"] != "none"]
    cleaned_tracks = cleaned_tracks.drop(columns=["track_name", "artist_name"])
    cleaned_tracks[["artist_id", "artist_name", "duration_ms", "track_name"]] = cleaned_tracks["track_id"].apply(lambda id : info.loc[id, :])
    return cleaned_tracks

def agg_tracks(info):
    tracks = {}
    history = {}

    # for track_id in ["2j4RC1LkwV47B0BMZNyvE3"]:
    for track_id in np.unique(info["track_id"]):
        listens = info[info["track_id"] == track_id]
        listens.loc[:, "count"] = 1
        
        artist_id = listens.iloc[0, listens.columns.get_loc("artist_id")]
        artist_name = listens.iloc[0, listens.columns.get_loc("artist_name")]
        song_name = listens.iloc[0, listens.columns.get_loc("track_name")]
        listen_count = listens.shape[0]
        listen_time = int(listens["ms_played"].sum())

        # TRACKS
        first_listen_row = listens[listens["timestamp"] == listens["timestamp"].min()]
        last_listen_row = listens[listens["timestamp"] == listens["timestamp"].max()]
        track_info = {
            "artist_id" : artist_id,
            "artist_name" : artist_name,
            "duration" : int(listens.iloc[0, listens.columns.get_loc("duration_ms")]),
            "first_listen" : {
                "hour": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("hour")]),
                "day": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("day")]),
                "weekday": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("weekday")]),
                "month": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("month")]),
                "year": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("year")]),
            },
            "last_listen" : {
                "hour": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("hour")]),
                "day": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("day")]),
                "weekday": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("weekday")]),
                "month": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("month")]),
                "year": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("year")]),
            },
            "listen_count" : listen_count,
            "listen_time" : listen_time,
            "listens": [],
            "song_name" : song_name,
            "track_id" : track_id,
        }

        for _, row in listens.iterrows():
            track_info["listens"].append({
                "hour": row["hour"],
                "day": row["day"],
                "weekday": row["weekday"],
                "month": row["month"],
                "year": row["year"],
                "duration": row["ms_played"]
            })
        tracks[track_id] = track_info

        # HISTORY
        listen_months = listens.loc[:, ["ms_played", "year_month", "count"]].groupby("year_month").sum()
        for year_month, row in listen_months.iterrows():
            year_month = f"{year_month}"
            year = int(year_month[0:4])
            month = int(year_month[4:6])
            if year not in history:
                history[year] = {}
            if month not in history[year]:
                history[year][month] = {
                    "listen_count": 0,
                    "listen_time": 0,
                    "uq_artists": set(),
                    "uq_songs": set(),
                }
            history[year][month]["listen_count"] += int(row["count"])
            history[year][month]["listen_time"] += int(row["ms_played"])
            history[year][month]["uq_artists"].add(artist_id)
            history[year][month]["uq_songs"].add(track_id)
                    
    for year in history:
        for month in history[year]:
            history[year][month]["uq_artists"] = list(history[year][month]["uq_artists"])
            history[year][month]["uq_songs"] = list(history[year][month]["uq_songs"])
    return tracks, history

def agg_artists(info):
    artists = {}
    artist_list = []

    # for artist_id in ["6Yv6OBXD6ZQakEljaGaDAk"]:
    for artist_id in np.unique(info["artist_id"]):
        listens = info[info["artist_id"] == artist_id]
        artist_name = listens.iloc[0, listens.columns.get_loc("artist_name")]

        first_listen_row = listens[listens["timestamp"] == listens["timestamp"].min()]
        last_listen_row = listens[listens["timestamp"] == listens["timestamp"].max()]

        artist_info = {
            "artist_id" : artist_id,
            "artist_name" : artist_name,
            "first_listen" : {
                "song_name" : first_listen_row.iloc[0, first_listen_row.columns.get_loc("track_name")],
                "track_id" : first_listen_row.iloc[0, first_listen_row.columns.get_loc("track_id")]
            },
            "first_listen_time" : {
                "hour": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("hour")]),
                "day": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("day")]),
                "weekday": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("weekday")]),
                "month": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("month")]),
                "year": int(first_listen_row.iloc[0, first_listen_row.columns.get_loc("year")]),
            },
            "last_listen" : {
                "song_name" : last_listen_row.iloc[0, last_listen_row.columns.get_loc("track_name")],
                "track_id" : last_listen_row.iloc[0, last_listen_row.columns.get_loc("track_id")]
            },
            "last_listen_time" : {
                "hour": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("hour")]),
                "day": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("day")]),
                "weekday": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("weekday")]),
                "month": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("month")]),
                "year": int(last_listen_row.iloc[0, last_listen_row.columns.get_loc("year")]),
            },
            "listen_count" : listens.shape[0],
            "listen_time" : int(listens["ms_played"].sum()),
            "tracks" : []
        }
        uq_tracks = listens.drop_duplicates(subset=["track_id"])
        for _, uq_track_row in uq_tracks.iterrows():
            artist_info["tracks"].append({
                "track_id" : uq_track_row["track_id"],
                "song_name" : uq_track_row["track_name"],
            })
        artists[artist_id] = artist_info

        # ARTIST LIST
        artist_list.append({
            "artist_id": artist_id,
            "artist_name": artist_name
        })

    return artists, artist_list

def get_fb_info():
    with open("firebase_songs.json", "r") as f:
        tracks = json.load(f)
    track_rows = []
    for track_id in tracks:
        artist_id = tracks[track_id]["artist_id"]
        artist_name = tracks[track_id]["artist_name"]
        duration = tracks[track_id]["duration"]
        song_name = tracks[track_id]["song_name"]
        for listen in tracks[track_id]["listens"]:
            month = listen["month"] if listen["month"] > 9 else f"0{listen['month']}"
            dt = datetime(listen["year"], listen["month"], listen["day"], listen["hour"], tzinfo=timezone.utc)
            timestamp = datetime.timestamp(dt)
            track_rows.append({
                "track_id": track_id,
                "artist_id": artist_id,
                "artist_name": artist_name,
                "duration_ms": duration,
                "track_name": song_name,
                "minute": 0,
                "hour": listen["hour"],
                "day": listen["day"],
                "month": listen["month"],
                "year": listen["year"],
                "year_month": f"{listen['year']}{month}",
                "weekday": listen["weekday"],
                "ms_played": listen["duration"],
                "timestamp": timestamp
            })
    return pd.DataFrame(track_rows)

if __name__ == "__main__":
    fb = FireManager()
    # ids = pd.read_csv("final_track_ids.csv", index_col="name")
    # info = get_info(ids)
    # fb_info = get_fb_info()
    # info = pd.concat((info, fb_info)).reset_index(drop=True)
    # tracks, history = agg_tracks(info)
    # artists, artist_list = agg_artists(info)
    # save_dict_json(tracks, "agg_tracks")
    # save_dict_json(history, "agg_history")
    # save_dict_json(artists, "agg_artists")
    # save_dict_json(artist_list, "agg_artist_list")
    tracks = read_dict_json("agg_tracks")
    history = read_dict_json("agg_history")
    artists = read_dict_json("agg_artists")
    artist_list = read_dict_json("agg_artist_list")

    # fb.set_artist_list(artist_list)

    # for year in history:
    #     fb.set_history(year, history[year])

    # for artist_id in artists:
    #     print(artist_id)
    #     fb.set_artist(artist_id, artists[artist_id])
    
    # for track_id in tracks:
    #     print(track_id)
    #     fb.set_track(track_id, tracks[track_id])



    