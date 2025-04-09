import requests
import base64
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_playlist_id(playlist_url):
    """Extract playlist ID from Spotify URL."""
    if "playlist/" in playlist_url:
        start_idx = playlist_url.find("playlist/") + len("playlist/")
        end_idx = playlist_url.find("?", start_idx) if "?" in playlist_url[start_idx:] else len(playlist_url)
        return playlist_url[start_idx:end_idx]
    return None

def get_token(id, secret):
    """Get Spotify API access token."""
    credentials = f"{id}:{secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        access_token = response.json()["access_token"]
        return access_token
    else:
        raise Exception(f"Error getting Spotify token: {response.json()}")

def get_from_playlist(playlist_id, access_token):
    """Get tracks from a Spotify playlist."""
    api_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        result = []
        # Get playlist details for title
        playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        playlist_response = requests.get(playlist_url, headers=headers)
        playlist_data = {}
        
        if playlist_response.status_code == 200:
            playlist_info = playlist_response.json()
            playlist_data = {
                "name": playlist_info.get("name", "Unknown Playlist"),
                "description": playlist_info.get("description", ""),
                "owner": playlist_info.get("owner", {}).get("display_name", "Unknown"),
                "total_tracks": playlist_info.get("tracks", {}).get("total", 0),
                "image_url": playlist_info.get("images", [{}])[0].get("url", "") if playlist_info.get("images") else ""
            }
        
        # Get track data
        tracks = []
        for item in response.json()["items"]:
            if not item["track"]:
                continue
                
            track = item["track"]
            track_name = track["name"]
            track_artists = [artist["name"] for artist in track["artists"]]
            
            if len(track_artists) >= 2:
                track_artists_str = track_artists[0] + " & " + track_artists[1]
            else:
                track_artists_str = track_artists[0] if track_artists else "Unknown Artist"
                
            merged = track_name + " - " + track_artists_str
            
            track_data = {
                "title": track_name,
                "artists": track_artists,
                "artists_str": track_artists_str,
                "search_query": merged,
                "duration_ms": track.get("duration_ms", 0),
                "album": track.get("album", {}).get("name", ""),
                "album_image": track.get("album", {}).get("images", [{}])[0].get("url", "") if track.get("album", {}).get("images") else ""
            }
            tracks.append(track_data)
            
        return {
            "playlist": playlist_data,
            "tracks": tracks
        }
    else:
        raise Exception(f"Error fetching playlist: {response.json().get('error', {}).get('message', 'Unknown error')}")

def process_spotify_playlist(playlist_url):
    """Process a Spotify playlist URL and return tracks data."""
    try:
        playlist_id = get_playlist_id(playlist_url)
        if not playlist_id:
            return {"success": False, "error": "Invalid Spotify playlist URL"}
            
        access_token = get_token(CLIENT_ID, CLIENT_SECRET)
        result = get_from_playlist(playlist_id, access_token)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}