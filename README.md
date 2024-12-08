# spotify_to_mp3 🎵

**spotify_to_mp3** is a Python script that converts Spotify playlists and tracks into MP3 files. By utilizing Spotify's API for track information and YouTube for downloading audio, it allows you to save music offline while retaining essential metadata like title, artist, and album art.

## Features
- 🎶 **Download MP3**: Convert Spotify tracks and playlists to MP3 files.
- 🖼️ **Metadata Tagging**: Automatically add track title, artist, album, and album art.
- 🌐 **YouTube Integration**: Fetch audio from YouTube for high-quality downloads.
- 🔗 **Spotify Integration**: Use Spotify's API for accurate track and playlist information.

## Requirements
- Python 3.8 or higher
- Spotify Developer Account (for API credentials)
- YouTube-DLP (for downloading audio)

## Installation

Step 1 **Clone the Repository**:
   ```bash
   git clone https://github.com/Sqmarshy/spotify_to_mp3.git
   cd spotify_to_mp3
   ```

Step 2 **Set Up a Virtual Environment (Optional)**:  
Setting up a virtual environment ensures that your dependencies are isolated and won’t interfere with other projects.
  ```bash
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

Step 3 **Install Dependencies**:  
Install the required Python libraries by running:
  ```bash
  pip install -r requirements.txt
  ```

Step 4 **Configure Spotify API**:  
Go to Spotify Developer and create an account.  
Create a new application and copy the Client ID and Client Secret.  
Set these values as environment variables:  
  ```bash
  export SPOTIFY_CLIENT_ID='your_client_id'
  export SPOTIFY_CLIENT_SECRET='your_client_secret'
  ```
On Windows, use:
  ```cmd
  set SPOTIFY_CLIENT_ID=your_client_id
  set SPOTIFY_CLIENT_SECRET=your_client_secret
  ```
Install YouTube-DLP:
YouTube-DLP is used to download audio from YouTube. Install it with:
  ```bash
  pip install youtube-dlp
  ```

## Usage
Downloads an entire playlist:
  ```bash
  python spotify_to_mp3.py --playlist-url "https://open.spotify.com/playlist/..."
  ```
output-dir: Specify the directory where MP3 files will be saved (default is ./downloads).  

## Troubleshooting
Ensure YouTube-DLP is installed and updated:
```bash
pip install -U youtube-dlp
```

Verify Spotify API credentials are correct and environment variables are set.
Ensure the required dependencies are installed:
```bash
pip install -r requirements.txt
```
## Disclaimer  
This tool is for personal use only. Downloading copyrighted content without permission may violate copyright laws. Ensure you comply with applicable laws and Spotify's terms of service.
