import requests
import base64
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PLAYLIST_URL = (
    "https://open.spotify.com/playlist/1m7ErQM1DDG4O0eFnsee0r?si=21ujVLt9SkeZu-FvNLTMog"
)
# PLAYLIST_URL = input('The url of the Spotify Playlist you like, please make sure it is public')


def get_playlist_id():
    start_idx = 34
    end_idx = 56
    return str(PLAYLIST_URL[start_idx:end_idx])


def get_token(id, secret):
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
        print("Access Token:", access_token)
        return access_token
    else:
        print("Error:", response.json())


def get_from_playlist(playlist_id, access_token):
    api_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        res = []
        for item in response.json()["items"]:
            track = item["track"]
            track_name = track["name"]
            track_artists = [artist["name"] for artist in track["artists"]]
            if len(track_artists) >= 2:
                track_artists = track_artists[0] + " & " + track_artists[1]
            else:
                track_artists = track_artists[0]
            merged = track_name + " - " + track_artists
            res.append(merged)
            print(f"Track: {track_name}, Artists: {track_artists}")
        return res
    else:
        print("Playlist provided may be a private playlist")
        print("Error:", response.json())


playlist_id = get_playlist_id()
access = get_token(CLIENT_ID, CLIENT_SECRET)
output = get_from_playlist(playlist_id, access)

new_folder = "data"
file_name = "query.csv"
if not os.path.exists(new_folder):
    os.makedirs(new_folder)
file_path = os.path.join(new_folder, file_name)
df = pd.DataFrame({"Queries": output})
df.to_csv(file_path, index=False, encoding="utf-8")
