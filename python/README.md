# Spotify Data Explorer
# Data Collection
These files are used to check when a song is listened to. When a song has finished playing, it is added to the Firestore database.

## firebase.py
This file handles all of the logic behind adding a listen to the Firestore Database. It also contains functions to download sections of the database as well as overwrite them

## gmail.py
This file contains logic to send an email. Since the script is running in the cloud forever, I need to be notified if any uncaught errors cause a crash. Otherwise it could be days before I notice something is wrong and I will have listened to many songs that went unrecorded. With this class I get an email anytime the script crashes.

## listen.py
This is the main file that runs forever in the cloud gathering the data. It contains the logic of connecting to the spotify API, determining when a song has finished, and parsing all of the information spotify provides about the song
