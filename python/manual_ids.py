import os
import json
import time

import pandas as pd
import numpy as np
import pyperclip

ALL = True
YEAR = False

def save_dict(track, filename):
    with open(f"{filename}.json", "w") as f:
        f.write(json.dumps(track))

def read_missing():
    f = open("no_results.txt", "r")
    rows = []
    for row in f:
        rows.append(row)
    f.close()
    return rows

if __name__ == "__main__":
    missing = read_missing()
    with open("new_track_ids.json", "r") as f:
        done = json.load(f)
    # done = {}
    track_ids = done
    idx = len(track_ids)
    for m in missing:
        song_name, info = m.rstrip("\n").split(" $BY$ ")
        artist_name, album_name = info.split(" $FROM$ ")
        key = f"{song_name} {artist_name}"
        if key not in done:
            pyperclip.copy(f"{song_name}")
            print(f"\n{idx}: Enter Track URI for {song_name} by {artist_name} from {album_name}")
            id = input()
            if id[0:7] == 'spotify':
                id = id.split(':')[2]
            elif id[0:5] == 'https':
                id = id.split('/')[-1]
            track_ids[key] = id
            print(id)
            save_dict(track_ids, "new_track_ids")
            idx += 1