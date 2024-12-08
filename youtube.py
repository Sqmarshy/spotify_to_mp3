import requests
import base64
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_youtube(query):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        items = response.json().get("items", [])
        if items:
            video_id = items[0]["id"]["videoId"]
            video_title = items[0]["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return {"title": video_title, "url": video_url}
        else:
            return {"error": "No results found"}
    else:
        return {
            "error": response.json().get("error", {}).get("message", "Unknown error")
        }


def search_tracks_on_youtube(tracks):
    res = {
        "Spotify Title and Artist": [],
        "Youtube Video Title": [],
        "Youtube Video URL": [],
    }
    for track in tracks:
        track_name = track
        result = search_youtube(track)
        if "error" not in result:
            print(f"Track: {track_name}")
            print(f"Title: {result['title']}")
            print(f"URL: {result['url']}\n")
            res["Spotify Title and Artist"].append(track)
            res["Youtube Video Title"].append(result["title"])
            res["Youtube Video URL"].append(result["url"])
        else:
            print(f"Error searching for {track_name}: {result['error']}")
    return res


df = pd.read_csv(r"data\query.csv")
output = list(df["Queries"])
youtube_name_and_urls = search_tracks_on_youtube(output)
df = pd.DataFrame(youtube_name_and_urls)
df.to_csv(r"data\youtube_urls.csv", index=False, encoding="utf-8")
print("Exported data in csv")
