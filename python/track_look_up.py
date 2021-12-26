import os
import pandas as pd
import json
import time

from spotify import Spotify

def print_json(info):
    with open(f"tracks_info.json", "w") as f:
        f.write(json.dumps(info))

if __name__ == "__main__":
    sp = Spotify()
    ids = pd.read_csv("final_track_ids.csv", index_col="name")
    ids = ids[ids["track_id"] != "none"]
    tracks = {}
    idx = 0
    total = ids.shape[0]
    for _, row in ids.iterrows():
        if idx % 100 == 0:
            print(f"{idx}/{total}")
        idx += 1
        result = sp.get_track(row["track_id"])
        tracks[row["track_id"]] = {
            'artist_id' : result["artists"][0]["id"],
            'artist_name' : result["artists"][0]["name"],
            'duration_ms' : result["duration_ms"],
            'track_name' : result["name"],
        }
        time.sleep(0.01)
    print_json(tracks)