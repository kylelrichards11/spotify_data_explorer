import os
import json
from datetime import datetime, timezone
import time
import re
import requests
import sys
import hashlib
import traceback

import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials

from gmail import Gmail
from firebase import FireManager, ServiceUnavailable

def print_track(track):
    with open(f"track.json", "w") as f:
        f.write(json.dumps(track))

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
        self.last_update_id = ''
        self.firebase = FireManager()
        self.id_map = {
            "Arctic Monkeys": "7Ln80lUS6He07XvHI8qqHH",
            "Hozier": "2FXC3k01G6Gw61bmprjgqS",
            "Joyner Lucas": "6C1ohJrd5VydigQtaGy5Wa",
            "Tash Sultana": "6zVFRTB0Y1whWyH7ZNmywf",
            "YUNGBLUD": "6Ad91Jof8Niiw0lGLLi3NW",
        }

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
            if info["artist_name"] in self.id_map:
                return self.id_map[info["artist_name"]]
            return hashlib.sha256(bytearray(f"{info['artist_name']}", 'utf-8')).hexdigest()
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
            return hashlib.sha256(bytearray(f"{info['song_name']}_{info['artist_name']}", 'utf-8')).hexdigest()
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
        
    def _should_release(self, current_id, last_id, last_track):
        """ Decides to release info for the last track or not 
        
        Parameters
        ----------
        current_id : str - the id of the currently playing song
        
        last_id : str - the id of the last played song

        last_track : dict - the info about the last track

        Returns
        -------
        boolean - True if info should be released false otherwise
        """
        
        # Check if song has changed
        if current_id == last_id:
            return False, None
        
        # Check if we just released this song
        if last_id == self.last_released_id:
            return False, None

        # Check if we just released anything
        now = datetime.now().timestamp()
        if now - self.last_released_sec <= 22:
            return False, None

        # Check if we listened to at least half of the song
        last_info = None
        if last_track["currently_playing_type"] == "track" or last_track["currently_playing_type"] is None:
            track_duration = self._get_track_duration(last_id)
            last_info = self._get_info(last_track, track_duration=track_duration)
            if track_duration > 0 and float(last_info["ms_played"])/float(track_duration) < 0.5:
                # Reset last_released_id to allow next song to be released if it is the same as the
                # previous song
                self.last_released_id = "0"
                return False, None

        self.last_released_id = id
        self.last_released_sec = now
        return True, last_info

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
        if track_id != self.last_update_id:
            self.last_update_id = track_id
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
        
        gmail = Gmail()
        last_track = self.spotify.current_user_playing_track()
        last_id = self._get_track_id(last_track)

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

                # Add info to database (if any)
                should_release, last_info = self._should_release(current_id, last_id, last_track)
                if should_release and last_info is not None:
                    artist_id = self._get_artist_id(last_track)
                    try:
                        self.firebase.add_song(last_id, artist_id, last_info)
                        self.firebase.add_to_week(last_id, artist_id, last_info)
                    except ServiceUnavailable as e:
                        print("Reinitializing Firebase")
                        self.firebase = FireManager()
                        time.sleep(5)
                        self.firebase.add_song(last_id, artist_id, last_info)
                        self.firebase.add_to_week(last_id, artist_id, last_info)
       
                self._update_current(current_id, current_track)

                # Update last_track
                last_id = current_id
                last_track = current_track

                # Wait 10 seconds
                time.sleep(10)

            # Check for errors
            except requests.exceptions.ReadTimeout as e:
                msg = f"ReadTimeout {e}"
                print(msg)
                time.sleep(30)
            except spotipy.exceptions.SpotifyException as e:
                try:
                    self.spotify = self._init_spotify()
                except:
                    tb = ''.join(traceback.format_tb(sys.exc_info()[2]))
                    msg = f"Could not init spotify: {sys.exc_info()[0]}\nTraceback:\n{tb}"
                    print(msg)
                    gmail.send_message(msg)
                    exit()
            except UnboundLocalError as e:
                tb = ''.join(traceback.format_tb(e.__traceback__))
                msg = f"Unbound Local Error {e}\nTraceback:\n{tb}"
                print(msg)
                gmail.send_message(msg)
                time.sleep(30)
            except:
                tb = ''.join(traceback.format_tb(sys.exc_info()[2]))
                msg = f"Unhandled Error: {sys.exc_info()[0]}\nTraceback:\n{tb}"
                print(msg)
                gmail.send_message(msg)
                raise

if __name__ == "__main__":
    listener = Listener()
    listener.listen()