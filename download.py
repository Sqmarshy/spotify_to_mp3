import os
import tempfile
import zipfile
from io import BytesIO
from yt_dlp import YoutubeDL

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

def create_youtube_playlist(video_ids, playlist_name, description=None):
    """
    Creates a YouTube playlist with the given videos.
    This is a placeholder - you would need to implement YouTube OAuth flow.
    """
    # This would require YouTube API OAuth 
    # Return a placeholder success response for now
    return {
        "success": True,
        "playlist_name": playlist_name,
        "video_count": len(video_ids),
        "playlist_url": "https://www.youtube.com/playlist?list=EXAMPLE"
    }