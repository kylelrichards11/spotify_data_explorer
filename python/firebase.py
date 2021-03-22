from datetime import datetime
import json

from google.cloud.firestore_v1 import Increment
from google.api_core.exceptions import ServiceUnavailable
import firebase_admin
from firebase_admin import credentials, firestore

def save_dict_json(my_dict, filename):
    with open(f"{filename}.json", "w") as f:
        f.write(json.dumps(my_dict))

class FireManager():
    """ Deals with all firebase interactions """
    def __init__(self):
        cred = credentials.Certificate("config.json")
        fb = firebase_admin.initialize_app(cred, {
            "project_id": "spotifydataexplorer-81773"
        })
        self.db = firestore.client()
        self.artist_collection = self.db.collection(u"artists")
        self.song_collection = self.db.collection(u"songs")
        self.artist_list_doc = self.db.collection(u"utils").document(u"artist_list")
        self.prev_week_doc = self.db.collection(u"overview").document(u"prev_week")
        self.prev_week_stage_doc = self.db.collection(u"overview").document(u"prev_week_stage")
        years = list(range(2013, 2022))
        years.remove(2014)
        self.history_collections = {}
        for year in years:
            self.history_collections[year] = self.db.collection(f"history_{year}")

    def _add_listen(self, artist_id, track_id, track_details):
        """ Adds a listen event to the firebase 
        
        Parameters
        ----------
        artist_id : str - the id of the song's artist

        track_id : str - the id of the song

        track_details : dict - the information to add to firebase about the listen

        Returns
        -------
        None
        
        """
        # Update Artist
        self.artist_collection.document(artist_id).update({
            "listen_count": Increment(1),
            "listen_time": Increment(track_details["ms_played"]),
            "last_listen_time": track_details["time_info"],
            "last_listen": {"track_id":track_id, "song_name":track_details["song_name"]}
        })

        # Update Song
        listen_info = self._get_time_info(track_details["timestamp"])
        listen_info["duration"] = track_details["ms_played"]
        self.song_collection.document(track_id).update({
            "listen_count": Increment(1),
            "listen_time": Increment(track_details["ms_played"]),
            "last_listen": track_details["time_info"],
            "listens": firestore.ArrayUnion([listen_info])
        })

        # Add to History
        self.history_collections[track_details['time_info']['year']].document(f"{track_details['time_info']['month']}").update({
            "listen_count": Increment(1),
            "listen_time": Increment(track_details["ms_played"]),
            "uq_artists": firestore.ArrayUnion([artist_id]),
            "uq_songs": firestore.ArrayUnion([track_id])
        })

    def _doc_to_dict(self, doc):
        """ Converts a document to a dictionary

        Parameters
        ----------
        doc : google.cloud.firestore_v1.document.DocumentReference - the document

        Returns
        -------
        dict - the document in dictionary form
        """
        return doc.get().to_dict()
        
    def _get_time_info(self, dt):
        """ Gets a dictionary of the elements of the datetime 
        
        Parameters
        ----------
        dt : datetime - the datetime object

        Returns
        -------
        dict - a dictionary of datetime components
        """
        info = {}
        info["year"] = dt.date().year
        info["month"] = dt.date().month
        info["day"] = dt.date().day
        info["weekday"] = dt.weekday()
        info["hour"] = dt.time().hour
        return info

    def _init_artist(self, artist_id, track_id, track_details):
        """ Adds a new artist to firebase for the first time 
        
        Parameters
        ----------
        artist_id : str - the id of the song's artist

        track_id : str - the id of the first song played

        track_details : dict - the information to add to firebase about the artist and first song

        Returns
        -------
        None
        """
        doc_ref = self.artist_collection.document(artist_id)
        doc_ref.set({
            "artist_id": artist_id,
            "artist_name": track_details["artist_name"],
            "first_listen_time": self._get_time_info(track_details["timestamp"]),
            "first_listen": {"track_id":track_id, "song_name":track_details["song_name"]},
            "listen_count": 0,
            "listen_time": 0,
            "tracks": [],
        })

        self.artist_list_doc.update({
            "list": firestore.ArrayUnion([{"artist_id":artist_id, "artist_name":track_details["artist_name"]}])
        })

    def _init_history(self, year):
        """ Adds the year to the history document in firebase 
        
        Parameters
        ----------
        year : str - the year to add

        Returns
        -------
        None
        """
        for month in range(1, 13):
            self.db.collection(f"history_{year}").document(f"{month}").set({
                "listen_count": 0,
                "listen_time": 0,
                "uq_artists": [],
                "uq_songs": []
            })
        self.history_collections[int(year)] = self.db.collection(f"history_{year}")

    def _init_song(self, artist_id, track_id, track_details):
        """ Adds a new song to firebase for the first time 
        
        Parameters
        ----------
        artist_id : str - the id of the song's artist

        track_id : str - the id of the song

        track_details : dict - the information to add to firebase about the song

        Returns
        -------
        None
        """
        song_doc_ref = self.song_collection.document(track_id)
        song_doc_ref.set({
            "artist_id": artist_id,
            "artist_name": track_details["artist_name"],
            "duration": track_details["duration"],
            "first_listen": self._get_time_info(track_details["timestamp"]),
            "song_name": track_details["song_name"],
            "track_id": track_id,
            "listens": []
        })

        artist_doc_ref = self.artist_collection.document(artist_id)
        artist_doc_ref.update({
            "tracks": firestore.ArrayUnion([{"track_id":track_id, "song_name":track_details["song_name"]}])
        })

    def add_song(self, track_id, artist_id, track_details):
        """ Adds a song to the firebase if it is not already in there. If it is, it increases the play count and time for the song and artist 
        
        Parameters
        ----------
        track_id : str - the id of the track

        artist_id : str - the id of the artist

        track_details : dict - the information about the track to add to firebase

        Returns
        -------
        None
        """
        if artist_id == "":
            artist_id = track_id
        track_details["time_info"] = self._get_time_info(track_details["timestamp"])

        # Check if artist exists
        artist = self.artist_collection.document(artist_id).get()
        if not artist.exists:
            self._init_artist(artist_id, track_id, track_details)

        # Check if song exists
        song = self.song_collection.document(track_id).get()
        if not song.exists:
            self._init_song(artist_id, track_id, track_details)

        # Increase stats
        self._add_listen(artist_id, track_id, track_details)

    def merge_tracks(self, track_id1, track_id2):
        """ Merges the listening information for two tracks that should be the same ids 
        
        Parameters
        ----------
        track_id1 : str - the track_id to merge into

        track_id2 : str - the track_id to merge from

        Returns
        -------
        None
        """
        track_1 = self.get_track_doc(track_id1)
        track_2 = self.get_track_doc(track_id2)
        save_dict_json(self._doc_to_dict(track_1), "track_1")
        save_dict_json(self._doc_to_dict(track_2), "track_2")

    def download_artists(self):
        """ Downloads and saves the artist documents as a dictionary to firebase_artists.json
        
        Paramaters
        ----------
        None

        Returns
        -------
        None
        """
        artist_dict = {}
        artist_docs = self.artist_collection.stream()
        for doc in artist_docs:
            artist_dict[doc.id] = doc.to_dict()
        save_dict_json(artist_dict, "firebase_artists")

    def download_artist_list(self):
        """ Downloads and saves the artist list as a dictionary to firebase_artist_list.json
        
        Paramaters
        ----------
        None

        Returns
        -------
        None
        """
        artist_list = self.artist_list_doc.get().to_dict()
        save_dict_json(artist_list, "firebase_artist_list")

    def download_history(self):
        """ Downloads and saves the artist list as a dictionary to firebase_history.json
        
        Paramaters
        ----------
        None

        Returns
        -------
        None
        """
        history_dict = {}
        for collection in self.history_collections:
            history_docs = collection.stream()
            for doc in history_docs:
                history_dict[collection.id][doc.id] = doc.to_dict()
        save_dict_json(history_dict, "firebase_history")

    def download_songs(self):
        """ Downloads and saves the song documents as a dictionary to firebase_songs.json
        
        Paramaters
        ----------
        None

        Returns
        -------
        None
        """
        song_dict = {}
        song_docs = self.song_collection.stream()
        for doc in song_docs:
            song_dict[doc.id] = doc.to_dict()
        save_dict_json(song_dict, "firebase_songs")

    def get_track_doc(self, track_id):
        """ Reads the specified track's document from firebase 
        
        Parameters
        ----------
        track_id : str - the id of the track

        Returns
        -------
        dict : the information stored in firebase about the track
        """
        return self.song_collection.document(track_id)

    def update_current(self, info):
        """ Updates the information at overview/current
        
        Parameters
        ----------
        info : dict - the fields and values to add

        Returns
        -------
        None
        
        """
        doc_ref = self.db.collection(u"overview").document(u"current")
        doc_ref.set(info)

    def set_artist(self, artist_id, artist_info):
        """ Sets the artist information at the given artist_id, overwriting any existing data 
        
        Parameters
        ----------
        artist_id : str - the id of the artist being added

        artist_info : dict - the information to sent to firebase
        
        Returns
        -------
        None
        """
        artist_doc_ref = self.artist_collection.document(artist_id)
        artist_doc_ref.set(artist_info)

    def set_artist_list(self, artist_list):
        """ Sets the entire artist_list information, overwriting any existing data 
        
        Parameters
        ----------
        artist_list : list - the information to sent to firebase
        
        Returns
        -------
        None
        """
        self.artist_list_doc.set({"list":artist_list})

    def set_history(self, history):
        """ Sets the entire history information, overwriting any existing data 
        
        Parameters
        ----------
        year : int - the year to add

        year_info : dict - the information to sent to firebase
        
        Returns
        -------
        None
        """
        for year in history:
            for month in history[year]:
                month_doc_ref = self.history_collections[int(year)].document(f"{month}")
                month_doc_ref.set(history[year][month])

    def set_track(self, track_id, track_info):
        """ Sets the track information at the given track_id, overwriting any existing data 
        
        Parameters
        ----------
        track_id : str - the id of the track being added

        track_info : dict - the information to sent to firebase
        
        Returns
        -------
        None
        """
        song_doc_ref = self.song_collection.document(track_id)
        song_doc_ref.set(track_info)

    def add_to_week(self, track_id, artist_id, track_details):
        """ Adds to previous week's list of songs
        """
        self.prev_week_doc.update({
            "tracks": firestore.ArrayUnion([{
                "artist_id": artist_id,
                "artist_name": track_details["artist_name"],
                "listen_time": track_details["ms_played"],
                "song_name": track_details["song_name"],
                "track_id": track_id,
                "timestamp": track_details["timestamp"]
            }])
        })

    def get_prev_week(self):
        """ Gets the previous week doc from firebase
        
        Parameters
        ----------
        None

        Returns
        -------
        dict - the previous week doc in a dictionary
        """
        return self.prev_week_doc.get().to_dict()

    def set_prev_week(self, tracks, stage=True):
        """ Sets the previous week doc to tracks

        Parameters
        ----------
        tracks (dict) : the tracks to add to prev week.

        stage (bool, default=True) : whether to write to stage or regular

        Returns
        -------
        None
        """
        doc = self.prev_week_stage_doc if stage else self.prev_week_doc
        doc.set(tracks)

    # def query_top_weekly(self, start, end, n=20):
    #     """ Returns the top 25 most played songs by listens in the given time interval
        
    #     Parameters
    #     ----------
    #     start : string in form YYYY-MM-DD

    #     end : 
        
    #     Returns
    #     -------
    #     None
    #     """
    #     start = datetime.strptime(start, "%Y-%m-%d")
    #     end = datetime.strptime(end, "%Y-%m-%d")
    #     query = self.prev_week_collection.order_by(u'listens').order_by(u'listen_time').limit(n)
    #     results = query.stream()
    #     print(results)
    #     for r in results:
    #         print(r.id)

if __name__ == "__main__":
    fb = FireManager()
    # fb.query_top_weekly("2021-03-07", "2021-03-08", 5)
    # with open("firebase_history_temp.json", "r") as f:
    #     history = json.load(f)
    # fb.set_history(history)
