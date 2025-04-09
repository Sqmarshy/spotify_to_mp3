import os
import tempfile
import zipfile
from io import BytesIO
from yt_dlp import YoutubeDL

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json

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

def get_authenticated_service():
    """Get an authenticated YouTube API service."""
    credentials = None
    
    # Look for saved credentials
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_info(
            json.loads(open('token.json').read()))
    
    # If no valid credentials, authenticate
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json', SCOPES)
        credentials = flow.run_local_server(port=8080)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    
    return build('youtube', 'v3', credentials=credentials)

def create_youtube_playlist(video_ids, playlist_name, description=None):
    try:
        # Get authenticated service
        youtube = get_authenticated_service()
        playlist_response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": description or f"Playlist created from Spotify2MP3: {playlist_name}",
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"  # Can be "public", "private", or "unlisted"
                }
            }
        ).execute()
        
        playlist_id = playlist_response["id"]
        
        # Add videos to the playlist
        videos_added = 0
        failed_video_ids = []
        
        for video_id in video_ids:
            try:
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
                videos_added += 1
            except HttpError as e:
                failed_video_ids.append({"id": video_id, "error": str(e)})
        
        # Return success result
        return {
            "success": True,
            "playlist_name": playlist_name,
            "playlist_id": playlist_id,
            "video_count": videos_added,
            "playlist_url": f"https://www.youtube.com/playlist?list={playlist_id}",
            "failed_videos": failed_video_ids
        }
        
    except HttpError as e:
        # Handle API errors
        return {
            "success": False,
            "error": f"An HTTP error occurred: {e.resp.status} {e.content}"
        }
    except Exception as e:
        # Handle any other exceptions
        return {
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }