import os
import pandas as pd
from yt_dlp import YoutubeDL

output_folder = "output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def download_as_mp3(links, output_folder=output_folder):
    """
    Downloads YouTube links as MP3 files.
    Args:
        links (list of str): List of YouTube video URLs.
        output_folder (str): Folder where MP3 files will be saved.
    """
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
        "outtmpl": "output/%(title)s.%(ext)s",
        "ffmpeg_location": r"C:\ffmpeg-7.1-essentials_build\bin",
        "quiet": False,
    }

    with YoutubeDL(options) as ydl:
        for link in links:
            try:
                print(f"Downloading: {link}")
                ydl.download([link])
            except Exception as e:
                print(f"Failed to download {link}: {e}")


data = pd.read_csv(r"data\youtube_urls.csv")
youtube_links = data["Youtube Video URL"]
spotify_name = data["Spotify Title and Artist"]
download_as_mp3(youtube_links)
