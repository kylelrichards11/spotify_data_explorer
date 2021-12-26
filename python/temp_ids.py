import pandas as pd

if __name__ == "__main__":
    old_ids = pd.read_csv("final_track_ids.csv", encoding="utf-8", index_col="name")
    print(old_ids)
    man_ids = pd.read_json("new_track_ids.json", orient="index", encoding="utf-8")
    man_ids.columns = ["track_id"]
    print(man_ids)
    ids = pd.read_csv("track_ids.csv", encoding="utf-8", index_col="name")
    ids = ids.drop(columns="Unnamed: 0")
    print(ids)
    final_ids = pd.concat((old_ids, ids, man_ids))
    print(final_ids)
    # final_ids.to_csv("final_track_ids.csv", index_label="name")
    