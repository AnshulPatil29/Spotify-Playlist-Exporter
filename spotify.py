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

# setup authmanager for authorization
# note that this does not call the API,this just sets it up for later
auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
) 
sp = spotipy.Spotify(auth_manager=auth_manager)


def id_helper_name(playlist_name:str,sp=sp)->str:
    results = sp.current_user_playlists(limit=50)
    while True:
        if results['items']:
            for item in results['items']:
                if 'name' in item and 'id' in item:
                    if item['name']==playlist_name:
                        return item['id']
        if results['next']:
            results = sp.next(results)
        else:
            return None
        
def id_helper_url(playlist_url:str)->str:
    return playlist_url[34:56]



def get_playlist_id(playlist:str,sp=sp)->str:
    '''
    returns: playlist id or '' for liked songs
    '''
    # playlist id is 22 characters long, and starts right after 'https://open.spotify.com/playlist/' which is 34 characters long
    if playlist.startswith('https://open.spotify.com/playlist'):
        return id_helper_url(playlist)
    
    if playlist is None or playlist=='':
        return ''
    
    result=id_helper_name(playlist,sp)
    if result is None:
        print('Playlist not found')
        exit()
    return result