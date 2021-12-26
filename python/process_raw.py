import json
import pandas as pd
import numpy as np

if __name__ == "__main__":
    f = open("data/AllSongs.json", "r")
    rows = []
    for row in f:
        r = json.loads(row) 
        rows.append(r)
    f.close()

    rows.reverse()

    df = pd.DataFrame(rows)
    df = df.drop(columns=['ip_addr_decrypted'])
    df = df.rename(columns={'master_metadata_track_name':'track_name', 'master_metadata_album_artist_name':'artist_name', 'master_metadata_album_album_name':'album_name'})
    df['offline'] = df['offline'].fillna(False)
    df['shuffle'] = df['shuffle'].fillna(False)
    df['skipped'] = df['skipped'].fillna(False)
    df.to_csv('processed_data.csv')