import requests
from dotenv import load_dotenv
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def generate_mock_youtube_results(tracks):
    """Generate mock YouTube results for testing when API is unavailable."""
    results = []
    
    for track in tracks:
        if isinstance(track, dict):
            title = track.get("title", "Unknown Title")
            artists = track.get("artists_str", "Unknown Artist")
            query = track.get("search_query", f"{title} - {artists}")
        else:
            query = str(track)
            title = query
            artists = ""
        
        # Create a mock result
        track_result = {
            "spotify_data": track,
            "youtube_title": f"[MOCK] {query} (Official Video)",
            "youtube_url": f"https://www.youtube.com/watch?v=mock-id-{hash(query) % 1000000:06d}",
            "youtube_id": f"mock-id-{hash(query) % 1000000:06d}",
            "match_quality": "good"  # Assume good matches for testing
        }
        results.append(track_result)
    
    return {
        "success": True,
        "results": results,
        "errors": [],
        "total_tracks": len(tracks),
        "matched_tracks": len(results),
        "failed_tracks": 0
    }

def search_youtube(query):
    """Search YouTube for a video matching the query."""
    url = "https://www.googleapis.com/youtube/v3/search"
    
    # Debug: Check if API key exists
    if not YOUTUBE_API_KEY:
        print("YouTube API key is missing. Please set the YOUTUBE_API_KEY environment variable.")
        return {"error": "YouTube API key not configured"}
    
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY,
    }

    try:
        print(f"Searching YouTube for: {query}")
        response = requests.get(url, params=params)
        
        # Debug: Print response status
        print(f"YouTube API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            # Debug: Check if items were returned
            print(f"YouTube returned {len(items)} items")
            
            if items:
                video_id = items[0]["id"]["videoId"]
                video_title = items[0]["snippet"]["title"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                return {"title": video_title, "url": video_url, "id": video_id}
            else:
                print(f"No YouTube results found for query: {query}")
                return {"error": "No results found"}
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            print(f"YouTube API error: {error_message}")
            return {"error": error_message}
    except Exception as e:
        print(f"Exception in YouTube search: {str(e)}")
        return {"error": f"Exception: {str(e)}"}

def search_tracks_on_youtube(tracks):
    """Search for multiple tracks on YouTube."""
    # Check if YouTube API key exists
    if not YOUTUBE_API_KEY:
        print("WARNING: YouTube API key is missing, returning mock results")
        # Generate mock results for testing
        return generate_mock_youtube_results(tracks)
    
    results = []
    errors = []
    
    for track in tracks:
        query = track.get("search_query") if isinstance(track, dict) else track
        result = search_youtube(query)
        
        if "error" not in result:
            track_result = {
                "spotify_data": track,
                "youtube_title": result["title"],
                "youtube_url": result["url"],
                "youtube_id": result["id"],
                "match_quality": evaluate_match_quality(track, result["title"])
            }
            results.append(track_result)
        else:
            errors.append({
                "track": track,
                "error": result["error"]
            })
    
    return {
        "success": len(results) > 0,
        "results": results,
        "errors": errors,
        "total_tracks": len(tracks),
        "matched_tracks": len(results),
        "failed_tracks": len(errors)
    }

def evaluate_match_quality(track, youtube_title):
    """Simple algorithm to evaluate match quality."""
    # This is a placeholder - you could implement a more sophisticated matching algorithm
    if isinstance(track, dict) and "title" in track and "artists_str" in track:
        title_lower = track["title"].lower()
        artist_lower = track["artists_str"].lower()
        youtube_lower = youtube_title.lower()
        
        if title_lower in youtube_lower and artist_lower in youtube_lower:
            return "good"
        elif title_lower in youtube_lower or artist_lower in youtube_lower:
            return "partial"
        else:
            return "poor"
    else:
        # Basic string matching if track is just a string
        track_str = track.lower() if isinstance(track, str) else ""
        youtube_lower = youtube_title.lower()
        
        if track_str and track_str in youtube_lower:
            return "good"
        else:
            return "poor"