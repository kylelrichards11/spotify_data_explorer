import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import os
import requests
import time

class Spotify():
    def __init__(self):
        self.username = "1275479048"
        self.sp = self._auth()
        self.top_25_playlist = "3gRC5uapfncEioUxJ6qThX"

    def _auth(self):
        client_id = os.environ["SPOTIPY_CLIENT_ID"]
        client_secret = os.environ["SPOTIPY_CLIENT_SECRET"]
        redirect_uri = "http://localhost:8888/callback"
        scope = "user-read-currently-playing user-read-recently-played playlist-modify-public"
        token = util.prompt_for_user_token(
            self.username, 
            scope, 
            client_id=client_id, 
            client_secret=client_secret, 
            redirect_uri=redirect_uri
        )
        return spotipy.Spotify(auth=token)

    def search_track(self, track_name=None, artist_name=None):
        """ Looks up a track with the spotify api. Must provide track name and artist name 

        Parameters
        ----------
        track_name : str - the name of the track
        
        artist_name : str - the name of the artist who wrote the track

        Returns
        -------
        list of dicts - the resulting info from spotify
        """
        assert(track_name is not None and artist_name is not None)
        try:
            return self.sp.search(q=f"artist:{artist_name} track:{track_name}", type='track')
        except requests.exceptions.ReadTimeout as e:
            msg = f"ReadTimeout {e}"
            print(msg)
            time.sleep(30)
            return self.search_track(track_name, artist_name)

    def get_track(self, id):
        """ Gets the track with the given spotify id 
        
        Parameters
        ----------
        id : str - the spotify id

        Returns
        -------
        dict - the information from spotify
        """
        try:
            return self.sp.track(id)
        except requests.exceptions.ReadTimeout as e:
            msg = f"ReadTimeout {e}"
            print(msg)
            time.sleep(30)
            return self.get_track(id)

    
    def _empty_week_playlist(self):
        """ Removes all songs from the top 25 playlist 
        
        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        items = self.sp.playlist_tracks(self.top_25_playlist, fields=["items"])["items"]
        ids = [item["track"]["id"] for item in items]
        self.sp.user_playlist_remove_all_occurrences_of_tracks(self.username, self.top_25_playlist, ids)

    def set_week_playlist(self, ids):
        """ Sets the songs in the top 25 playlist to the given ids

        Parameters
        ----------
        ids : list - the ids of tracks to add to the playlist

        Returns
        -------
        None
        """
        self._empty_week_playlist()
        self.sp.user_playlist_add_tracks(self.username, self.top_25_playlist, ids)
