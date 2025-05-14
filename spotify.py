import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import json

# import client id, secret and URI from config.json
try:
    with open('config.json','r') as f:
        spotify_data=json.load(f)['SPOTIFY']
    CLIENT_ID=spotify_data['CLIENT_ID']
    CLIENT_SECRET=spotify_data['CLIENT_SECRET']
    REDIRECT_URI=spotify_data['REDIRECT_URI']
except (FileNotFoundError, KeyError) as e:
    print(f"Error loading configuration from config.json: {e}")
    exit()
    

# define the access that the Oauth Provides from SpotifyAPI
SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
) 
sp = spotipy.Spotify(auth_manager=auth_manager)
