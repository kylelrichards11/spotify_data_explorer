import os
import json
import time

import pandas as pd
import numpy as np
from spotify import Spotify

ALL = False
YEAR = True

def save_dict(track, filename):
    with open(f"{filename}.json", "w") as f:
        f.write(json.dumps(track))

def read_all_tracks():
    f = open("../data/AllSongs.json", "r")
    rows = []
    for row in f:
        r = json.loads(row) 
        rows.append(r)
    f.close()
    rows.reverse()
    return rows

def save_tracks(sp, known_ids, uq_tracks):
    track_ids = []
    idx = 1
    for _, row in uq_tracks.iterrows():
        # if idx % 100 == 0:
        #     print(f"{idx}/{uq_tracks.shape[0]}")
        idx += 1
        track = row["track_name"]
        artist = row["artist_name"]
        album = row["album_name"] if "album_name" in uq_tracks.columns else ""
        key = f"{track} {artist}"
        if key not in known_ids.index:
            result = sp.search_track(track_name=track, artist_name=artist)
            if result is None or len(result["tracks"]["items"]) == 0:
                print(f"{track} $BY$ {artist} $FROM$ {album}")
            else:
                track_ids.append([key, result["tracks"]["items"][0]["id"]])
            time.sleep(0.01)

    track_ids = pd.DataFrame(track_ids, columns=["name", "track_id"])
    track_ids.to_csv("track_ids.csv")

def add_all(sp, known_ids):
    tracks = read_all_tracks()
    tracks = pd.DataFrame(tracks)
    tracks = tracks.loc[:, ["master_metadata_track_name", "master_metadata_album_artist_name", "master_metadata_album_album_name"]]
    tracks.columns = ["track_name", "artist_name", "album_name"]
    tracks = tracks.dropna(subset=["track_name", "artist_name"])
    uq_tracks = tracks.drop_duplicates(subset=["track_name", "artist_name"]).reset_index(drop=True)
    save_tracks(sp, known_ids, uq_tracks)

def read_year_tracks():
    data = []
    for file_num in range(1, 4):
        with open(f"../data/2020_year_data/StreamingHistory{file_num}.json") as f:
            data.extend(json.load(f))
    return pd.DataFrame(data)

def add_year(sp, known_ids):
    tracks = read_year_tracks()
    tracks = tracks.drop(columns=["msPlayed", "endTime"])
    tracks.columns = ["artist_name", "track_name"]
    tracks = tracks.dropna(subset=["track_name", "artist_name"])
    uq_tracks = tracks.drop_duplicates(subset=["track_name", "artist_name"]).reset_index(drop=True)
    save_tracks(sp, known_ids, uq_tracks)

if __name__ == "__main__":
    sp = Spotify()
    known_ids = pd.read_csv("final_track_ids.csv", index_col=0)
    if ALL:
        add_all(sp, known_ids)
    elif YEAR:
        add_year(sp, known_ids)