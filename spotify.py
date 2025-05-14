import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import os

# define the access that the Oauth Provides from SpotifyAPI
scopes = "user-library-read playlist-read-private playlist-read-collaborative" 
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes))

