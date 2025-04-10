import os
import tempfile
import zipfile
from io import BytesIO
from yt_dlp import YoutubeDL
import json

# For YouTube OAuth2
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

def download_as_mp3(links, output_folder=None):
    """
    Downloads YouTube links as MP3 files.
    Args:
        links (list of str): List of YouTube video URLs.
        output_folder (str): Folder where MP3 files will be saved.
    Returns:
        list: Paths of downloaded files
    """
    if output_folder is None:
        output_folder = tempfile.mkdtemp()
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Configure yt-dlp
    options = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": os.path.join(output_folder, "%(title)s.%(ext)s"),
        "ffmpeg_location": r"C:\ffmpeg-7.1-essentials_build\bin",  # Consider making this configurable
        "quiet": False,
    }
    
    downloaded_files = []
    failed_downloads = []
    
    with YoutubeDL(options) as ydl:
        for link in links:
            try:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                downloaded_files.append(filename)
            except Exception as e:
                failed_downloads.append({"url": link, "error": str(e)})
    
    return {
        "success": len(downloaded_files) > 0,
        "downloaded_files": downloaded_files,
        "failed_downloads": failed_downloads,
        "download_folder": output_folder
    }

def create_zip_from_mp3s(folder_path):
    """
    Creates a zip file containing all MP3 files in the given folder.
    Args:
        folder_path (str): Path to folder containing MP3 files.
    Returns:
        BytesIO: In-memory zip file
    """
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.mp3'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.basename(file_path)  # Use just the filename in the archive
                    zipf.write(file_path, arcname=arcname)
    
    memory_file.seek(0)
    return memory_file

SCOPES = ['https://www.googleapis.com/auth/youtube']

def get_youtube_credentials(run_auth_flow=False, store_in_session=None):
    """
    Gets OAuth2 credentials for YouTube API.
    
    Args:
        run_auth_flow (bool): Whether to run the OAuth flow if no credentials exist
        store_in_session (dict, optional): Session dict to store credentials in
        
    Returns:
        tuple: (credentials, result_dict)
    """
    # Location to store credentials
    creds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials')
    if not os.path.exists(creds_dir):
        os.makedirs(creds_dir)
        
    token_path = os.path.join(creds_dir, 'youtube_token.pickle')
    credentials = None
    
    # Check if token file exists
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            try:
                credentials = pickle.load(token)
            except:
                # If token loading fails, we'll recreate it
                pass
                
    # If credentials are invalid or don't exist, refresh or create new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except:
                # If refresh fails, we'll recreate the credentials
                credentials = None
                
        # If we still don't have valid credentials, need to go through OAuth flow
        if not credentials and run_auth_flow:
            # Path to client secrets file from Google Developer Console
            client_secrets_path = os.path.join(creds_dir, 'client_secrets.json')
            
            if not os.path.exists(client_secrets_path):
                return None, {
                    "success": False, 
                    "error": "Missing client_secrets.json file. Please download it from Google Developer Console.",
                    "setup_required": True
                }
                
            try:
                # Create the flow using client secrets file and required scopes
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path,
                    ['https://www.googleapis.com/auth/youtube']
                )
                
                # Get the credentials by running the OAuth flow
                credentials = flow.run_local_server(port=0)
                
                # Save the credentials for next time
                with open(token_path, 'wb') as token:
                    pickle.dump(credentials, token)
                
                # Store in session if requested
                if store_in_session is not None:
                    store_in_session['youtube_credentials'] = credentials
                    
            except Exception as e:
                return None, {
                    "success": False,
                    "error": f"Authentication failed: {str(e)}"
                }
                
    return credentials, {"success": True}

def create_youtube_playlist(video_ids, playlist_name, description=None, session_data=None):
    """
    Creates a YouTube playlist with the given videos.
    Uses OAuth2 to authenticate with the YouTube API.
    
    Args:
        video_ids (list): List of YouTube video IDs.
        playlist_name (str): Name for the playlist.
        description (str, optional): Description for the playlist.
        session_data (dict, optional): Session data containing credentials
        
    Returns:
        dict: Result of creating the playlist.
    """
    # Check if credentials are in the session
    credentials = None
    if session_data and 'youtube_credentials' in session_data:
        credentials = session_data['youtube_credentials']
        
    # If not, get credentials from file
    if not credentials:
        credentials, creds_result = get_youtube_credentials()
        if not creds_result["success"]:
            return creds_result
    
    try:
        # Build the YouTube API client
        youtube = googleapiclient.discovery.build(
            'youtube', 'v3', credentials=credentials, cache_discovery=False
        )
        
        # Create the playlist
        playlists_insert_response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": description or f"Playlist created from Spotify2MP3 for {playlist_name}",
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"  # Can be "public", "private", or "unlisted"
                }
            }
        ).execute()
        
        playlist_id = playlists_insert_response["id"]
        
        # Add videos to the playlist
        for video_id in video_ids:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()
        
        # Get playlist URL
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        return {
            "success": True,
            "playlist_name": playlist_name,
            "playlist_id": playlist_id,
            "playlist_url": playlist_url,
            "video_count": len(video_ids)
        }
        
    except googleapiclient.errors.HttpError as e:
        error_content = json.loads(e.content)
        error_message = error_content.get('error', {}).get('message', str(e))
        return {
            "success": False,
            "error": f"YouTube API error: {error_message}",
            "error_details": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "error_details": str(e)
        }