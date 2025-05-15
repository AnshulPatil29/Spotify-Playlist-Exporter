import spotipy
from spotipy.oauth2 import SpotifyPKCE 
import pandas as pd
import json
import tkinter as tk 
from tkinter import filedialog, messagebox 
import sys 
import os 
from appdirs import user_cache_dir

# helper function for pyinstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



CONFIG_FILE = resource_path('config.json')
CLIENT_ID = None
REDIRECT_URI = None

APP_NAME = "SpotifyPlaylistExporter"
APP_AUTHOR = "MySpotifyTools"
CACHE_DIR = user_cache_dir(APP_NAME, APP_AUTHOR)
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
    except OSError as e:
        print(f"Warning: Could not create cache directory at {CACHE_DIR}: {e}")
        CACHE_DIR = "." 
SPOTIFY_CACHE_PATH = os.path.join(CACHE_DIR, '.spotify_pkce_cache')

try:
    with open(CONFIG_FILE, 'r') as f:
        spotify_data = json.load(f)['SPOTIFY']
    CLIENT_ID = spotify_data['CLIENT_ID']
    REDIRECT_URI = spotify_data['REDIRECT_URI']
except (FileNotFoundError, KeyError) as e:
    print(f"CRITICAL ERROR: Error loading configuration from {CONFIG_FILE}: {e}")

SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
DEFAULT_ATTRIBUTES = ['id', 'name', 'artists.name', 'album.name', 'album.album_type', 'album.release_date', 'duration_ms']

sp_global = None
auth_manager_global = None

def initialize_spotify_auth()->bool:
    """
    Initializes the Spotify Authentication Manager and the Spotipy client.
    Attempts to get an access token.
    Returns True on success, False on failure.
    """
    global auth_manager_global, sp_global, CLIENT_ID, REDIRECT_URI, SCOPE, SPOTIFY_CACHE_PATH

    if not CLIENT_ID or not REDIRECT_URI: 
        messagebox.showerror("Configuration Error", "Client ID or Redirect URI is missing. Please check config.json.")
        return False

    try:
        auth_manager_global = SpotifyPKCE(
            client_id=CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=True,
            cache_path=SPOTIFY_CACHE_PATH
        )
        token_info = auth_manager_global.get_access_token() 
        if not token_info:
            messagebox.showerror("Authentication Failed", "Could not get Spotify access token. Please try again.")
            return False
        sp_global = spotipy.Spotify(auth_manager=auth_manager_global)
        return True
    except Exception as e:
        messagebox.showerror("Authentication Error", f"Could not initialize Spotify: {e}")
        sp_global = None 
        return False

def id_helper_name(playlist_name: str) -> str | None:
    """
    Finds playlist ID by name. 
    Uses global sp_global.
    """
    if not sp_global: return None 
    results = sp_global.current_user_playlists(limit=50)
    while results:
        for item in results['items']:
            if item.get('name', '').lower() == playlist_name.lower(): 
                return item.get('id')
        results = sp_global.next(results) if results['next'] else None
    return None

def id_helper_url(playlist_url: str) -> str :
    """Extracts playlist ID from URL."""
    return playlist_url[34:56]


def get_playlist_id_from_query(playlist_query: str) -> str | None:
    """
    Determines playlist ID from user query (name, URL, or blank for liked).
    Returns playlist ID, '' for liked songs, or None if not found/invalid.
    """
    if not sp_global:
        messagebox.showerror("Error", "Spotify not authenticated. Please authenticate first.")
        return None

    if not playlist_query: 
        return ''

    if 'open.spotify.com/playlist/' in playlist_query:
        return id_helper_url(playlist_query)
    else: 
        return id_helper_name(playlist_query)


def get_tracks_to_df(playlist_id: str, attributes: list[str]) -> pd.DataFrame | None:
    """Fetches tracks and converts them to a DataFrame. Uses global sp_global."""
    if not sp_global: return None

    output_columns = []
    attribute_to_output_mapping = []
    col_idx_counter = 0

    for attr_path in attributes:
        if attr_path == 'artists.name':
            output_columns.extend(['primary-artist', 'featured-artists'])
            attribute_to_output_mapping.append({'type': 'artists', 'indices': (col_idx_counter, col_idx_counter + 1)})
            col_idx_counter += 2
        else:
            output_columns.append(attr_path.replace('.', '-')) 
            attribute_to_output_mapping.append({'type': 'other', 'path': attr_path, 'index': col_idx_counter})
            col_idx_counter += 1
    all_rows_data=[] 
    items_iterator=None
    if playlist_id=='': 
        items_iterator=sp_global.current_user_saved_tracks(limit=50)
    else:
        items_iterator=sp_global.playlist_items(playlist_id, limit=50, fields="items(track(id,name,artists(name),album(name,album_type,release_date),duration_ms)),next")


    while items_iterator:
        for item in items_iterator['items']:
            track_data=item.get('track')
            if not track_data or track_data.get('id') is None:
                continue

            row_data=[None]*len(output_columns)

            for mapping in attribute_to_output_mapping:
                if mapping['type']=='artists':
                    artists=track_data.get('artists', [])
                    if artists:
                        row_data[mapping['indices'][0]]=artists[0].get('name')
                        if len(artists)>1:
                            row_data[mapping['indices'][1]]=", ".join([a.get('name') for a in artists[1:]])
                else:
                    current_val = track_data
                    for part in mapping['path'].split('.'):
                        if isinstance(current_val, dict):
                            current_val = current_val.get(part)
                        else:
                            current_val = None
                            break
                    row_data[mapping['index']] = current_val
            all_rows_data.append(row_data)

        items_iterator = sp_global.next(items_iterator) if items_iterator.get('next') else None
    if not all_rows_data:
        return pd.DataFrame(columns=output_columns)
    return pd.DataFrame(all_rows_data, columns=output_columns)


def export_data_to_excel(main_df: pd.DataFrame, update_excel_path: str | None = None):
    """Saves the DataFrame to Excel, handles update logic, and creates multiple sheets."""
    if main_df.empty and not update_excel_path:
        messagebox.showinfo("No Data", "No data to export.")
        return

    output_filename_suggestion = "spotify_playlist_data.xlsx"
    final_sheets = {'AllSongs': main_df.copy()} 
    if update_excel_path:
        try:
            old_df = pd.read_excel(update_excel_path, sheet_name='AllSongs')
            if 'id' not in old_df.columns or 'id' not in main_df.columns:
                messagebox.showerror("Update Error", "'id' column missing in existing or new data. Cannot update.")
                output_filename_suggestion = "spotify_playlist_data_new_only.xlsx"
            else:
                old_ids = set(old_df['id'].dropna())
                new_ids = set(main_df['id'].dropna())
                missing_in_new_df = old_df[old_df['id'].isin(old_ids - new_ids)]
                newly_added_to_playlist_df = main_df[main_df['id'].isin(new_ids - old_ids)]
                combined_df = pd.concat([main_df, missing_in_new_df], ignore_index=True).drop_duplicates(subset=['id'], keep='first')
                final_sheets['AllSongs'] = combined_df

                if not missing_in_new_df.empty:
                    final_sheets['MissingFromCurrentPlaylist'] = missing_in_new_df
                if not newly_added_to_playlist_df.empty:
                    final_sheets['NewlyAddedToPlaylist'] = newly_added_to_playlist_df
                
                output_filename_suggestion = update_excel_path.split('/')[-1].replace(".xlsx", "_updated.xlsx")


        except FileNotFoundError:
            messagebox.showwarning("Update Warning", f"Update file '{update_excel_path}' not found. Proceeding to save new data only.")
            output_filename_suggestion = "spotify_playlist_data_new.xlsx"
        except Exception as e:
            messagebox.showerror("Update Error", f"Error during update: {e}")
    save_path = filedialog.asksaveasfilename(
        initialfile=output_filename_suggestion,
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
    )
    if not save_path:
        messagebox.showinfo("Cancelled", "Export operation cancelled.")
        return

    try:
        with pd.ExcelWriter(save_path) as writer:
            for sheet_name, df_to_write in final_sheets.items():
                if not df_to_write.empty:
                     df_to_write.to_excel(writer, sheet_name=sheet_name, index=False)
        messagebox.showinfo("Success", f"Data successfully exported to\n{save_path}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Could not save Excel file: {e}")

class SpotifyExporterApp:
    def __init__(self, root_window):
        """
        Initializes the Spotify Exporter Application UI.
        Args:
            root_window (tk.Tk): The main window for the Tkinter application.
        """
        self.root = root_window
        self.root.title("Spotify Playlist Exporter")
        try:
        # Use resource_path to find the bundled icon
            icon_path = resource_path('app_icon.ico')
            self.root.iconbitmap(icon_path)
        except tk.TclError:
            # This can happen if the .ico file is not found, corrupt,
            # or on some OS configurations.
            print("Warning: Could not set window icon. Ensure 'app_icon.ico' is bundled correctly.")
        # stores boolean variable for checkboxes
        self.attribute_vars = {} 
        self.is_authenticated = False 
        if CLIENT_ID and REDIRECT_URI: #
            if initialize_spotify_auth():
                self.is_authenticated = True
        else:
            messagebox.showerror("Fatal Configuration Error",
                                 f"CLIENT_ID or REDIRECT_URI missing. Please check '{CONFIG_FILE}'.\nApplication will now close.")
            self.root.destroy() 
            return 

        self._setup_ui_layout()
        self._update_ui_auth_state() 

    def _setup_ui_layout(self):
        """Creates and arranges all the UI widgets."""

        auth_frame = tk.Frame(self.root, pady=5)
        auth_frame.pack(fill=tk.X, padx=10)

        self.auth_status_label = tk.Label(auth_frame, text="Status: Checking...", fg="orange")
        self.auth_status_label.pack(side=tk.LEFT, padx=5)

        self.login_button = tk.Button(auth_frame, text="Login / Re-Login to Spotify", command=self._handle_spotify_login)
        self.login_button.pack(side=tk.RIGHT, padx=5)

        attr_outer_frame = tk.Frame(self.root, padx=10, pady=5)
        attr_outer_frame.pack(fill=tk.X)
        attr_frame = tk.LabelFrame(attr_outer_frame, text="Select Attributes to Export")
        attr_frame.pack(fill=tk.X)

        num_cols = 3
        for i, attr_name in enumerate(DEFAULT_ATTRIBUTES):
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(attr_frame, text=attr_name, variable=var)
            chk.grid(row=i // num_cols, column=i % num_cols, sticky="w", padx=5, pady=2)
            self.attribute_vars[attr_name] = var

        playlist_frame = tk.LabelFrame(self.root, text="Playlist Source", padx=10, pady=5)
        playlist_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(playlist_frame, text="Playlist Name/Link (or blank for Liked Songs):").pack(side=tk.LEFT, padx=(0,5))
        self.playlist_entry = tk.Entry(playlist_frame) 
        self.playlist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        update_frame = tk.LabelFrame(self.root, text="Update Existing Excel (Optional)", padx=10, pady=5)
        update_frame.pack(fill=tk.X, padx=10, pady=5)

        self.update_path_var = tk.StringVar()
        update_path_display = tk.Entry(update_frame, textvariable=self.update_path_var, state='readonly', width=50)
        update_path_display.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        browse_button = tk.Button(update_frame, text="Browse...", command=self._select_update_excel_file)
        browse_button.pack(side=tk.LEFT, padx=(0,5))
        clear_button = tk.Button(update_frame, text="Clear", command=lambda: self.update_path_var.set(""))
        clear_button.pack(side=tk.LEFT)


        process_button_frame = tk.Frame(self.root, pady=10)
        process_button_frame.pack()
        self.process_button = tk.Button(process_button_frame, text="Get Playlist Data & Export to Excel", command=self._trigger_processing_and_export, font=("Arial", 10, "bold"))
        self.process_button.pack()

        self.status_var = tk.StringVar() 
        self.status_var.set("Please log in to Spotify if needed.")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padx=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_ui_auth_state(self):
        """Updates UI elements based on Spotify authentication status."""
        if self.is_authenticated:
            self.auth_status_label.config(text="Status: Authenticated with Spotify", fg="green")
            self.process_button.config(state=tk.NORMAL) 
            self.status_var.set("Ready. Select options and export.")
        else:
            self.auth_status_label.config(text="Status: Not Authenticated", fg="red")
            self.process_button.config(state=tk.DISABLED) 
            self.status_var.set("Please log in to Spotify to enable export.")

    def _handle_spotify_login(self):
        """Handles the 'Login / Re-Login to Spotify' button click."""
        self.status_var.set("Attempting Spotify authentication... Follow browser prompts.")
        self.root.update_idletasks()

        if initialize_spotify_auth():
            self.is_authenticated = True
            messagebox.showinfo("Authentication Success", "Successfully authenticated with Spotify!")
        else:
            self.is_authenticated = False
        self._update_ui_auth_state() 

    def _select_update_excel_file(self):
        """Opens a file dialog to select an Excel file for updating."""
        filepath = filedialog.askopenfilename(
            title="Select Excel file to update",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            self.update_path_var.set(filepath)
            self.status_var.set(f"Selected update file: {filepath.split('/')[-1]}")

    def _trigger_processing_and_export(self):
        """
        Main function triggered by the 'Process & Export' button.
        It gathers inputs from the UI and calls the backend processing functions.
        """
        if not self.is_authenticated or not sp_global:
            messagebox.showerror("Not Authenticated", "Please authenticate with Spotify first using the Login button.")
            self._update_ui_auth_state()
            return

        selected_attributes = [attr for attr, var in self.attribute_vars.items() if var.get()]
        if not selected_attributes:
            messagebox.showwarning("No Attributes Selected", "Please select at least one attribute to export.")
            return
        playlist_query = self.playlist_entry.get().strip()
        update_file_path = self.update_path_var.get() if self.update_path_var.get() else None

        self.status_var.set("Processing: Getting playlist ID...")
        self.root.update_idletasks()
        playlist_id = get_playlist_id_from_query(playlist_query) 

        if playlist_id is None and playlist_query != "": 
            messagebox.showerror("Playlist Not Found", f"Could not find playlist: '{playlist_query}'.\nPlease check the name/link or leave blank for Liked Songs.")
            self.status_var.set("Playlist not found. Ready.")
            return
        self.status_var.set(f"Processing: Fetching tracks for '{playlist_query if playlist_query else 'Liked Songs'}'...")
        self.root.update_idletasks()

        current_df = get_tracks_to_df(playlist_id, selected_attributes) 

        if current_df is None:
            self.status_var.set("Error fetching tracks. Please check messages. Ready.")
            return

        if current_df.empty and playlist_id != '':
             messagebox.showinfo("No Tracks", f"No tracks found in the playlist '{playlist_query}'. The playlist might be empty or only contain unreadable tracks.")
             self.status_var.set("No tracks found in specified playlist. Ready.")
        elif current_df.empty and playlist_id == '':
            messagebox.showinfo("No Tracks", "No tracks found in your Liked Songs.")
            self.status_var.set("No tracks found in Liked Songs. Ready.")

        self.status_var.set("Processing: Preparing Excel export...")
        self.root.update_idletasks()
        export_data_to_excel(current_df, update_excel_path=update_file_path) 
        self.status_var.set("Export process finished. Ready for next operation.")

if __name__ == "__main__":
    if not CLIENT_ID or not REDIRECT_URI:
        try:
            root_error = tk.Tk()
            root_error.withdraw() 
            messagebox.showerror("Fatal Configuration Error",
                                 f"CLIENT_ID or REDIRECT_URI missing. Please check '{CONFIG_FILE}'.\nApplication cannot start.")
            root_error.destroy()
        except tk.TclError: 
            print(f"FATAL UI ERROR: Could not show Tkinter messagebox for missing config. Check '{CONFIG_FILE}'.")
        sys.exit(1) 

    root = tk.Tk() 
    app = SpotifyExporterApp(root) 
    root.mainloop()