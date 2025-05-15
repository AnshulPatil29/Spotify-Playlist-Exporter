# Spotify Playlist Exporter

**Export your Spotify playlists and liked songs to Excel with ease!**

A simple desktop application built with Python, Tkinter, Spotipy, and Pandas that allows you to fetch track details from your Spotify playlists (or your "Liked Songs") and export them into a structured Excel file. Features include selecting specific track attributes and updating existing Excel files with new/missing songs.

## Disclaimer
* This app will currently only work if I whitelist a user as it runs in development mode.
* Which is why I highly recommend anyone who is interested on using this application to download the files from the `local-app` branch. You only need the spotify.py and config.py, and need to setup the config and dev dashboard for Spotify API
* This is currently a work in progress

## Features

* **Export Liked Songs:** Easily download details of all your liked tracks.
* **Export Playlists:**
  * By Playlist Name: Just type the name of your playlist.
  * By Playlist URL/Link: Paste the direct link to the playlist.
* **Customizable Attributes:** Select which track attributes you want to export (e.g., ID, Name, Artist, Album, Release Date, Duration).
* **Update Existing Excel Files:**
  * Provide an existing exported Excel file, and the app will update it.
  * Identifies newly added songs to the playlist.
  * Identifies songs that were in the old Excel but are now missing from the current playlist.
* **Organized Excel Output:** Exports data into sheets like 'AllSongs', 'NewlyAddedToPlaylist', and 'MissingFromCurrentPlaylist' for easy analysis.
* **User-Friendly GUI:** Simple graphical interface, no command-line needed for basic use.
* **PKCE Authentication:** Uses Spotify's secure PKCE flow for authentication.

## Installation (for End-Users)

1. **Download the latest release:**
   * Go to the [Releases Page](https://github.com/AnshulPatil29/Spotify-Playlist-Exporter/releases).
   * Download the `SpotifyPlaylistExporter.exe` file (or the `.zip` file if you provide a one-folder bundle).
2. **Place the EXE:**
   * Move `SpotifyPlaylistExporter.exe` to any convenient location on your computer (e.g., your Desktop or a dedicated applications folder).
3. **Run the Application:**
   * Double-click `SpotifyPlaylistExporter.exe` to start.
   * The application bundles the necessary Spotify Client ID. On first launch (or if your authentication token expires), you will be redirected to your web browser to log in and authorize the application with Spotify.

## How to Use

1. **Launch the Application:** Run `SpotifyPlaylistExporter.exe`.
2. **Authenticate (if prompted):**
   * A "Login / Re-Login to Spotify" button will be available. If the status shows "Not Authenticated," click this button.
   * Your web browser will open to the Spotify authorization page. Log in and grant permission.
   * You'll be redirected (usually to a `localhost` address), and the app should show "Status: Authenticated."
   * *Note: Since this is the single-file EXE version, Spotify authentication may be required each time you open the app as the cache is stored temporarily.*
3. **Select Attributes:** Check the boxes for the track details you wish to export.
4. **Playlist Source:**
   * **To export your Liked Songs:** Leave the "Playlist Name/Link" field blank.
   * **To export a specific playlist:**
     * Enter the exact **Playlist Name** as it appears in your Spotify.
     * OR, paste the full **Playlist Link/URL** (e.g., `https://open.spotify.com/playlist/your_playlist_id?...`).
5. **Update Existing Excel (Optional):**
   * If you have a previously exported Excel file from this tool and want to update it:
     * Click "Browse..." and select your existing `.xlsx` file.
     * The path to the selected file will appear. You can "Clear" it if you change your mind.
6. **Process & Export:**
   * Click the "Get Playlist Data & Export to Excel" button.
   * The application will fetch the track data.
   * A "Save As" dialog will appear. Choose a location and filename for your new Excel file.
7. **Done!** A success message will confirm the export.

## Configuration

The application uses a `config.json` file which is **bundled within the executable**. This file contains the necessary Spotify `CLIENT_ID` and `REDIRECT_URI` required for the PKCE authentication flow.

* **CLIENT_ID:** This is public and specific to this application instance.
* **REDIRECT_URI:** This is set to `http://127.0.0.1:8888/callback` which is a loopback as configured in the Spotify Developer Dashboard for this application.

End-users do not need to modify this configuration to use the pre-compiled executable.

## Building from Source (for Developers)

If you want to modify the code or build the executable yourself:

1. **Prerequisites:**
   
   * Python 3.8+
   * Conda (recommended for managing environments)
   * Git

2. **Clone the Repository:**
   
   ```bash
   git clone https://github.com/AnshulPatil29/Spotify-Playlist-Exporter.git
   cd Spotify-Playlist-Exporter
   ```

3. **Set up the Python Environment:**
   
   * **Using Conda (recommended):**
     
     ```bash
     conda env create -f environment.yml  # If an environment.yml is provided
     conda activate spotify_exporter_env 
     ```

4. **Configuration (`config.json`):**
   
   * The repository includes a `config.json` file with the public `CLIENT_ID` and `REDIRECT_URI`. If you are forking and creating your own Spotify App, you would update this file with your own credentials from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   * Ensure your `REDIRECT_URI` in `config.json` exactly matches one you've added to your app settings on the Spotify Developer Dashboard.

5. **Run the Script:**
   
   ```bash
   python spotify.py
   ```

6. **Build the Executable (using PyInstaller):**
   
   * The `SpotifyPlaylistExporter.spec` file is provided and configured for building.
   
   * Ensure PyInstaller is installed (`pip install pyinstaller`).
   
   * From the project root directory, run:
     
     ```bash
     pyinstaller SpotifyPlaylistExporter.spec
     ```
   
   * Alternatively, to generate the `.spec` file initially and build:
     
     ```bash
     pyinstaller --name SpotifyPlaylistExporter --onefile --windowed --add-data "config.json:." your_script_name.py
     ```
   
   * The executable will be found in the `dist/` folder.

## Future Work
- Need to update the front end to not give option of removing id from possible attributes as it is required for playlist update feature
- Need to add a feature to create a playlist based on an excel file with song ID's


## Acknowledgements

* [Spotipy](https://spotipy.readthedocs.io/) - For the Python library to interact with the Spotify Web API.
* [Pandas](https://pandas.pydata.org/) - For data manipulation and Excel export.
* [Tkinter](https://docs.python.org/3/library/tkinter.html) - For the GUI.
* [PyInstaller](https://www.pyinstaller.org/) - For packaging the application.

---

Made by [Anshul Patil/AnshulPatil29]
