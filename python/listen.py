import os
import json
from datetime import datetime, timezone
import time
import re
import requests

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from google.cloud.firestore_v1 import Increment
from google.api_core.exceptions import ServiceUnavailable
import firebase_admin
from firebase_admin import credentials, firestore

def print_track(track):
    with open(f"track.json", "w") as f:
        f.write(json.dumps(track))

class FireManager():
    """ Deals with all firebase interactions """
    def __init__(self):
        cred = credentials.Certificate("config.json")
        fb = firebase_admin.initialize_app(cred, {
            "project_id": "spotifydataexplorer-81773"
        })
        self.db = firestore.client()

    def _add_listen(self, artist_collection, song_collection, history_doc, artist_id, track_id, track_details):
        """ Adds a listen event to the firebase 
        
        Parameters
        ----------
        aritst_collection : firestore.collection - the collection for the song's artist

        song_collection : firestore.collection - the collection for the song

        history_doc : firestore.document - the firestore document representing the history document

        artist_id : str - the id of the song's artist

        track_id : str - the id of the song

        track_details : dict - the information to add to firebase about the listen

        Returns
        -------
        None
        
        """
        # Update Artist
        artist_collection.document(artist_id).update({
            "listen_count": Increment(1),
            "listen_time": Increment(track_details["ms_played"]),
            "last_listen_time": track_details["time_info"],
            "last_listen": {"track_id":track_id, "song_name":track_details["song_name"]}
        })

        # Update Song
        listen_info = self._get_time_info(track_details["timestamp"])
        listen_info["duration"] = track_details["ms_played"]
        song_collection.document(track_id).update({
            "listen_count": Increment(1),
            "listen_time": Increment(track_details["ms_played"]),
            "last_listen": track_details["time_info"],
            "listens": firestore.ArrayUnion([listen_info])
        })

        # Add to History
        history_doc.update({
            f"{track_details['time_info']['year']}" : {
                f"{track_details['time_info']['month']}" : {
                    "listen_count": Increment(1),
                    "listen_time": Increment(track_details["ms_played"]),
                    "uq_artists": firestore.ArrayUnion([{"artist_id":artist_id, "artist_name":track_details["artist_name"]}]),
                    "uq_songs": firestore.ArrayUnion([{"track_id":track_id, "song_name":track_details["song_name"]}])
                }
            }
        })
        
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

    def _init_artist(self, artist_collection, artist_id, track_id, track_details):
        """ Adds a new artist to firebase for the first time 
        
        Parameters
        ----------
        aritst_collection : firestore.collection - the collection for the song's artist

        artist_id : str - the id of the song's artist

        track_id : str - the id of the first song played

        track_details : dict - the information to add to firebase about the artist and first song

        Returns
        -------
        None
        """
        doc_ref = artist_collection.document(artist_id)
        doc_ref.set({
            "artist_id": artist_id,
            "artist_name": track_details["artist_name"],
            "first_listen_time": self._get_time_info(track_details["timestamp"]),
            "first_listen": {"track_id":track_id, "song_name":track_details["song_name"]},
            "listen_count": 0,
            "listen_time": 0,
            "tracks": [],
        })

        self.db.collection(u"utils").document(u"artist_list").update({
            "list": firestore.ArrayUnion([{"artist_id":artist_id, "artist_name":track_details["artist_name"]}])
        })

    def _init_history(self, history_doc, year):
        """ Adds the year to the history document in firebase 
        
        Parameters
        ----------
        history_doc : firestore.document - the firestore document representing the history document

        year : int - the year to add

        Returns
        -------
        None
        """
        months = {}
        for month in range(1, 13):
            months[f"{month}"] = {
                "listen_count": 0,
                "listen_time": 0,
                "uq_artists": [],
                "uq_songs": []
            }
        history_doc.update({
            f"{year}": months
        })

    def _init_song(self, artist_collection, song_collection, artist_id, track_id, track_details):
        """ Adds a new song to firebase for the first time 
        
        Parameters
        ----------
        aritst_collection : firestore.collection - the collection for the song's artist

        song_collection : firestore.collection - the collection for the song

        artist_id : str - the id of the song's artist

        track_id : str - the id of the song

        track_details : dict - the information to add to firebase about the song

        Returns
        -------
        None
        """
        song_doc_ref = song_collection.document(track_id)
        song_doc_ref.set({
            "artist_id": artist_id,
            "artist_name": track_details["artist_name"],
            "duration": track_details["duration"],
            "first_listen": self._get_time_info(track_details["timestamp"]),
            "song_name": track_details["song_name"],
            "track_id": track_id,
            "listens": []
        })

        artist_doc_ref = artist_collection.document(artist_id)
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
        track_details["time_info"] = self._get_time_info(track_details["timestamp"])

        # Check if artist exists
        artist_collection = self.db.collection(u"artists")
        artist = artist_collection.document(artist_id).get()
        if not artist.exists:
            self._init_artist(artist_collection, artist_id, track_id, track_details)

        # Check if song exists
        song_collection = self.db.collection(u"songs")
        song = song_collection.document(track_id).get()
        if not song.exists:
            self._init_song(artist_collection, song_collection, artist_id, track_id, track_details)

        # Check if history year exists
        year = track_details["time_info"]["year"]
        history_doc = self.db.collection(u"utils").document(u"history")
        history = history_doc.get().to_dict()
        if f"{year}" not in history:
            self._init_history(history_doc, year)

        # Increase stats
        self._add_listen(artist_collection, song_collection, history_doc, artist_id, track_id, track_details)

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

class Listener():
    """ Listens to the spotify songs and to give a notification of a new song being listened to
    
    Parameters
    ----------
    None
    
    """

    def __init__(self):
        self.spotify = self._init_spotify()
        self.last_released_id = ''
        self.last_released_sec = 0
        self.last_current_update_id = ''
        self.firebase = FireManager()

    def _add_to_firebase(self, info):
        """ Adds the listened to track to the json file 
        
        Parameters
        ----------
        info : tuple - the tuple of information for the song to add

        Returns
        -------
        None

        """
        artist_name, track_name, dt_str, ms_played = info
        info_dict = {"artist_name":artist_name, "track_name":track_name, "ms_played":ms_played}
        dt_str = re.sub(r':[0-9][0-9] UTC', '', dt_str)
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        info_dict["year"] = dt.date().year
        info_dict["month"] = dt.date().month
        info_dict["day"] = dt.date().day
        info_dict["weekday"] = dt.weekday()
        info_dict["hour"] = dt.time().hour
        info_dict["minute"] = dt.time().minute
        info_dict["year_month"] = f"{info_dict['year']}{0 if info_dict['month'] < 10 else ''}{info_dict['month']}"
        info_dict["timestamp"] = int(dt.timestamp())
        print(f"{track_name} by {artist_name}")
        with open(f"recent.json", "a+") as f:
            f.write(json.dumps(info_dict))

    def _check_if_podcast(self, track):
        """ Checks if the track is a podcast
        
        Parameters
        ----------
        track : dict - the dictionary of information returned by the spotify current_user_playing_track endpoint
        
        Returns
        -------
        bool - True if a podcast, False otherwise
        """
        if track["currently_playing_type"] == "episode":
            return True
        return False

    def _get_artist_id(self, track):
        """ Gets the ids of the artist of the song. The id is either the spotify provided id or the artist name if there is none 
        
        Parameters
        ----------
        track : dict - the dictionary of information returned by the spotify current_user_playing_track endpoint

        Returns
        -------
        id : str - the id for the artist

        """
        id = track["item"]["artists"][0]["id"]
        if id is None:
            info = self._get_info(track)
            return info["artist_name"]
        return id

    def _get_info(self, track, track_duration=0):
        """ Gets the song name, artist name, end time, and time played from the spotify dictionary returned from the api for the current_user_playing_track endpoint

        Parameters
        ----------
        track : dict - the dictionary of information returned by the spotify current_user_playing_track endpoint

        track_duration : int (default=0) - the duration of the song in milliseconds

        Returns
        -------
        dict - the artist name, song name, timestamp, and ms played of the track

        """
        artist_name = track["item"]["artists"][0]["name"]
        song_name = track["item"]["name"]

        ms_played = track["progress_ms"]

        if track_duration > 0 and (track_duration - ms_played) < 11000:
            ms_played = track_duration

        timestamp = datetime.fromtimestamp((track["timestamp"] + ms_played)/1000, tz=timezone.utc)
        
        return {
            "artist_name" : artist_name,
            "duration" : track_duration,
            "ms_played" : ms_played,
            "song_name" : song_name,
            "timestamp" : timestamp,
        }

    def _get_track_details(self, track_id, track):
        """ Gets the length of the song with the specified id 
        
        Parameters
        ----------
        track_id : str - the spotify id of the song

        track : dict - the dictionary of information returned by the spotify current_user_playing_track endpoint

        Returns
        -------
        dict : the spotify details of the track
        """
        try:
            details = {
                "artist_id" : self._get_artist_id(track),
                "artist_name" : track["item"]["artists"][0]["name"],
                "song_name" : track["item"]["name"],
                "track_id" : track_id
            }
            details["album_img"] = track["item"]["album"]["images"][0]["url"]
            return details
        except IndexError as e:
            details["album_img"] = "assets/default_img.png"
            return details

    def _get_track_duration(self, track_id):
        """ Gets the duration of the track in ms from the spotify api. If the track is not found 0 is returned 
        
        Parameters
        ----------
        track_id : str - the spotify id of the track

        Returns
        -------
        int - the length of the song in milliseconds
        """
        try:
            info = self.spotify.track(track_id)
            return info["duration_ms"]
        except requests.exceptions.ReadTimeout as e:
            print(e)
            return 0
        except spotipy.exceptions.SpotifyException as e:
            # Track not found
            if e.code == -1:
                return 0
            # Otherwise token expired
            self.spotify = self._init_spotify()
            return self._get_track_duration(track_id)

    def _get_track_id(self, track):
        """ Gets the id of the song. The id is either the spotify provided id or the song name and artist name concatenated if there is none 
        
        Parameters
        ----------
        track : dict - the dictionary of information returned by the spotify current_user_playing_track endpoint

        Returns
        -------
        id : str - the id for the track

        """
        id = track["item"]["id"]
        if id is None:
            info = self._get_info(track)
            return f"{info['song_name']}_{info['artist_name']}"
        return id

    def _init_spotify(self):
        """ Gets the auth token for my acount from spotify"""
        print("Getting new token")
        username = "1275479048"
        client_id = os.environ["SPOTIPY_CLIENT_ID"]
        client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
        redirect_uri = "http://localhost:8888/callback"
        scope = "user-read-currently-playing user-read-recently-played"
        token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
        return spotipy.Spotify(auth=token)
        
    def _should_release(self, id):
        """ Decides to release info or not 
        
        Parameters
        ----------
        id : str - the id of the last currently playing song

        Returns
        -------
        boolean - True if info should be released false otherwise

        """
        now = datetime.now().timestamp()
        if id != self.last_released_id or now - self.last_released_sec > 22:
            self.last_released_id = id
            self.last_released_sec = now
            return True
        return False

    def _update_current(self, track_id, track):
        """ Updates the track currently being listened to
        
        Parameters
        ----------
        track_id : str - the unique id of the track

        track : dict - the song name, artist name, and album image link of the track

        Returns
        -------
        None
        
        """
        if track_id != self.last_current_update_id:
            track_details = self._get_track_details(track_id, track)
            track_details["track_id"] = track_id
            self.firebase.update_current(track_details)

    def listen(self):
        """ Listens to the songs and outputs info whenever a new song has been listened to

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        
        last_current = self.spotify.current_user_playing_track()
        last_current_id = self._get_track_id(last_current)

        while True:
            try:
                # Read current track from api
                current_track = self.spotify.current_user_playing_track()
                while current_track is None:
                    time.sleep(10)
                    current_track = self.spotify.current_user_playing_track()

                if current_track is None or current_track["item"] is None or self._check_if_podcast(current_track):
                    continue

                current_id = self._get_track_id(current_track)
                self._update_current(current_id, current_track)

                # Save info if current changed
                last_info = None
                if current_id != last_current_id and last_current["currently_playing_type"] == "track":
                    track_duration = self._get_track_duration(last_current_id)
                    last_info = self._get_info(last_current, track_duration=track_duration)

                # Add info to json (if any)
                should_release = self._should_release(last_current_id) if last_info is not None else False
                if should_release:
                    artist_id = self._get_artist_id(last_current)
                    try:
                        self.firebase.add_song(last_current_id, artist_id, last_info)
                    except ServiceUnavailable as e:
                        print("Reinitializing Firebase")
                        self.firebase = FireManager()
                        time.sleep(5)
                        self.firebase.add_song(last_current_id, artist_id, last_info)

                # Update last
                last_current_id = current_id
                last_current = current_track

                # Wait 10 seconds
                time.sleep(10)

            except requests.exceptions.ReadTimeout as e:
                print(e)
                time.sleep(20)
            except spotipy.exceptions.SpotifyException as e:
                self.spotify = self._init_spotify()


if __name__ == "__main__":
    listener = Listener()
    listener.listen()