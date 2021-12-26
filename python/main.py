import json
import re
from datetime import datetime

import pandas as pd
import numpy as np

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

def read_all_tracks():
    f = open("../data/AllSongs.json", "r")
    rows = []
    for row in f:
        r = json.loads(row) 
        rows.append(r)
    f.close()
    rows.reverse()
    return rows

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
    tracks_songs = tracks_songs.groupby('track_name').sum()
    tracks_artists = tracks.drop(columns=["track_name", "day", "minute", "play_id"])
    tracks_artists = tracks_artists.groupby('artist_name').sum()
    return tracks_songs, tracks_artists

def clean_all(tracks):
    df = pd.DataFrame(tracks)
    df = df.rename(columns={'master_metadata_track_name':'track_name', 'master_metadata_album_artist_name':'artist_name', 'ts':'end_time'})
    df = df.loc[:, ['track_name', 'artist_name', 'ms_played', 'end_time']]
    df = df.dropna()
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
    df = df.drop(columns=['end_time'])
    return df    

def get_artist_songs(tracks):
    tracks = tracks.loc[:, ["artist_name", "track_name"]]
    tracks = tracks.drop_duplicates()
    tracks = tracks.groupby("artist_name")['track_name'].apply(list)
    return tracks

if __name__ == "__main__":
    tracks = read_all_tracks()
    cleaned_tracks = clean_all(tracks)
    cleaned_tracks = cleaned_tracks.iloc[0:100, :]
    write_df_dict(cleaned_tracks, f"../data/all_cleaned.json")

    # grouped_songs, grouped_artists = group(cleaned_tracks)
    # artist_songs = get_artist_songs(cleaned_tracks)

    # write_df_dict(grouped_songs, f"{PATH}/grouped_songs.json")
    # write_df_dict(grouped_artists, f"{PATH}/grouped_artists.json")
    # write_df_dict(artist_songs, f"{PATH}/artist_songs.json")

    # with open(f'{PATH}/overview.json', 'w') as f:
    #     f.write(json.dumps(overview))