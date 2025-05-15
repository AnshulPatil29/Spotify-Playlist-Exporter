import spotipy
from spotipy.oauth2 import SpotifyPKCE
import pandas as pd
import json
# import client id, secret and URI from config.json
try:
    with open('config.json','r') as f:
        spotify_data=json.load(f)['SPOTIFY']
    CLIENT_ID=spotify_data['CLIENT_ID']
    REDIRECT_URI=spotify_data['REDIRECT_URI']
except (FileNotFoundError, KeyError) as e:
    print(f"Error loading configuration from config.json: {e}")
    exit()
    
# define the access that the Oauth Provides from SpotifyAPI
SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
ATTRIBUTES = ['id','name','artists.name','album.name','album.album_type','album.release_date','duration_ms']

# ------------------------------------------------------------------------------------------------------------------
# setup authmanager for authorization
# note that this does not call the API,this just sets it up for later
auth_manager=SpotifyPKCE(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    open_browser=True
) 
auth_manager.get_access_token()
sp = spotipy.Spotify(auth_manager=auth_manager)
# ------------------------------------------------------------------------------------------------------------------

def id_helper_name(playlist_name:str,sp_instance:spotipy.Spotify=sp)->str:
    results = sp_instance.current_user_playlists(limit=50)
    while True:
        if results['items']:
            for item in results['items']:
                if 'name' in item and 'id' in item:
                    if item['name']==playlist_name:
                        return item['id']
        if results['next']:
            results = sp_instance.next(results)
        else:
            return None
                
def id_helper_url(playlist_url:str)->str:
    return playlist_url[34:56]

def get_playlist_id(playlist:str,sp_instance:spotipy.Spotify=sp)->str:
    '''
    returns: playlist id or '' for liked songs
    '''
    # playlist id is 22 characters long, and starts right after 'https://open.spotify.com/playlist/' which is 34 characters long
    if playlist.startswith('https://open.spotify.com/playlist'):
        return id_helper_url(playlist)
    
    if playlist is None or playlist=='':
        return ''
    
    result=id_helper_name(playlist,sp_instance)
    if result is None:
        print('Playlist not found')
        return None
    return result
# ------------------------------------------------------------------------------------------------------------------
# now we can fetch songs

def get_tracks_to_df(ID:str,attributes:list[str],sp_instance:spotipy.Spotify=sp)->pd.DataFrame:
    '''
    ID: ID of playlist, empty string for liked songs
    attributes: these are the fields that are pulled from track and stored in db
    sp_instance: Authorizing spotipy.Spotify module
    '''
    # I wanted to add a behaviour of primary artist and featured, which is why there a lot of unusually written code here
    output_columns=[]
    attribute_to_output_mapping=[]
    temp_idx_counter=0

    for attr in attributes:
        if attr == 'artists.name':
            output_columns.extend(['primary-artist','featured-artists'])
            attribute_to_output_mapping.append({'type': 'artists', 
                                                'original': attr, 
                                                'indices': (temp_idx_counter, temp_idx_counter + 1)})
            temp_idx_counter+=2
        else:
            output_columns.append(attr.replace('.','-'))
            attribute_to_output_mapping.append({'type':'other',
                                                'original':attr,
                                                'indices':temp_idx_counter})
            temp_idx_counter+=1

    data_lists = [[] for _ in range(len(output_columns))]

    # initial fetch based on ID
    if ID=='':
        result=sp_instance.current_user_saved_tracks(limit=50)
    else:
        result=sp_instance.playlist_items(ID,limit=50)


    while result:
        for item in result['items']:
            track_data=item.get('track')
            # missing track handling
            if not track_data:  
                for i in range(len(attributes)):
                    data_lists[i].append(None)
                continue
            
            # this is a loooong work around to handle artists
            for mapping_info in attribute_to_output_mapping:
                original_attribute=mapping_info['original']
                
                if mapping_info['type']=='artists':
                    primary_idx,featured_idx=mapping_info['indices']
                    artists_list = track_data.get('artists', [])
                    primary_artist_name = None
                    featured_names_list = []
                    if artists_list:
                        primary_artist_name=artists_list[0].get('name')
                        if len(artists_list)>1:
                            for i in range(1,len(artists_list)):
                                featured_names_list.append(artists_list[i].get('name'))
                    data_lists[primary_idx].append(primary_artist_name)
                    data_lists[featured_idx].append(",".join(featured_names_list) if featured_names_list else None)
                
                else:
                    data_idx=mapping_info['indices']
                    if '.' in original_attribute:
                        tag,subtag=original_attribute.split('.')
                        value=track_data.get(tag).get(subtag)
                    else:
                        value=track_data.get(original_attribute)
                    data_lists[data_idx].append(value)
        # get next page if it exists
        if result['next']:
            result=sp_instance.next(result)
        else:
            result=None




    dataframe={}
    for column,data in zip(output_columns,data_lists):
        dataframe[column]=data
    return pd.DataFrame(dataframe)
# ------------------------------------------------------------------------------------------------------------------
playlist_input=input('Enter playlist name or link, or leave it empty for liked songs: ')
ID=get_playlist_id(playlist_input)
while ID is None:
    playlist_input=input('Invalid Input Try Again')
    ID=get_playlist_id(playlist_input)
df=get_tracks_to_df(ID,ATTRIBUTES,sp) 


def get_excel(df:pd.DataFrame,update:str=None):
    if update is None:
        try:
            df.to_excel('spotify-data.xlsx', index=False,sheet_name='AllSongs') 
            print("DataFrame successfully saved to spotify-data.xlsx")
        except Exception as e:
            print(f"Error saving DataFrame to Excel: {e}")
    else:
        old_df=pd.read_excel(update,sheet_name='AllSongs')
        old_track_id_series = old_df['id']
        new_track_id_series = df['id']
        old_ids_set = set(old_track_id_series)
        new_ids_set = set(new_track_id_series)
        missing_from_new_ids_set = old_ids_set - new_ids_set  
        newly_added_ids_set = new_ids_set - old_ids_set      
        missing_df=old_df[old_df['id'].isin(missing_from_new_ids_set)]
        newly_added_df=df[df['id'].isin(newly_added_ids_set)]
        if not missing_df.empty:
            main_df=pd.concat([df, missing_df], ignore_index=True)
        else:
            main_df=df.copy()
        output_path=update[:-5]+'-udpated'+'.xlsx'
        with pd.ExcelWriter(output_path) as writer:
            main_df.to_excel(writer,sheet_name='AllSongs',index=False)
            if not missing_df.empty:
                missing_df.to_excel(writer,sheet_name='missing-songs')
            else:
                df.to_excel(writer,sheet_name='missing-songs')
            if not newly_added_df.empty:
                newly_added_df.to_excel(writer,sheet_name='newly-added')
            else:
                df.to_excel(writer,sheet_name='newly-added')

get_excel(df)

