from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
import uuid

# Import functions from our other modules
from spotify import process_spotify_playlist
from youtube import search_tracks_on_youtube
from download import download_as_mp3, create_zip_from_mp3s, create_youtube_playlist

app = Flask(__name__, template_folder='templates')
app.secret_key = "spotify_to_mp3_secret_key"

# Store active sessions and download results
sessions = {}

@app.route('/')
def index():
    """Home page with form to enter Spotify playlist URL"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_playlist():
    """Process the Spotify playlist URL and display tracks"""
    playlist_url = request.form.get('playlist_url')
    
    if not playlist_url:
        flash('Please enter a Spotify playlist URL', 'error')
        return redirect(url_for('index'))
    
    # Process Spotify playlist to get tracks
    spotify_result = process_spotify_playlist(playlist_url)
    
    if not spotify_result['success']:
        flash(f'Error processing Spotify playlist: {spotify_result["error"]}', 'error')
        return redirect(url_for('index'))
    
    # Create a session ID for this playlist
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'playlist_data': spotify_result['data'],
        'playlist_name': spotify_result['data']['playlist']['name'],
        'spotify_tracks': spotify_result['data']['tracks']
    }
    
    # Render the spotify tracks selection template
    return render_template('spotify_tracks.html', 
                          tracks=spotify_result['data']['tracks'],
                          playlist=spotify_result['data']['playlist'],
                          session_id=session_id)

@app.route('/search_youtube/<session_id>', methods=['POST'])
def search_youtube(session_id):
    """Search YouTube for selected Spotify tracks"""
    if session_id not in sessions:
        flash('Session expired or not found', 'error')
        return redirect(url_for('index'))
    
    # Get selected track indices from form
    selected_indices = request.form.getlist('selected_tracks')
    
    if not selected_indices:
        flash('Please select at least one track to search', 'error')
        return redirect(url_for('index'))
    
    # Convert indices to integers
    selected_indices = [int(idx) for idx in selected_indices]
    
    # Get the tracks from session data
    all_tracks = sessions[session_id]['spotify_tracks']
    selected_tracks = [all_tracks[idx] for idx in selected_indices if idx < len(all_tracks)]
    
    # Search YouTube for matches
    youtube_results = search_tracks_on_youtube(selected_tracks)
    
    if not youtube_results['success']:
        flash('Failed to find YouTube matches for the selected tracks', 'error')
        return redirect(url_for('index'))
    
    # Prepare results for the template
    results = []
    for item in youtube_results['results']:
        track_data = item['spotify_data']
        result = {
            'spotify_track': track_data['title'],
            'spotify_artists': track_data['artists_str'],
            'spotify_query': track_data.get('search_query', f"{track_data['title']} - {track_data['artists_str']}"),
            'youtube_title': item['youtube_title'],
            'youtube_url': item['youtube_url'],
            'youtube_id': item['youtube_id'],
            'match_quality': item['match_quality']
        }
        results.append(result)
    
    # Update session with YouTube results
    sessions[session_id]['youtube_results'] = results
    sessions[session_id]['youtube_errors'] = youtube_results['errors']
    
    # Render the YouTube results template
    return render_template('results.html', 
                          results=results, 
                          session_id=session_id,
                          playlist_name=sessions[session_id]['playlist_name'])

@app.route('/download/<session_id>', methods=['POST'])
def download_tracks(session_id):
    """Download selected tracks as MP3 files"""
    if session_id not in sessions:
        flash('Session expired or not found', 'error')
        return redirect(url_for('index'))
    
    selected_tracks = request.form.getlist('download_tracks')
    
    if not selected_tracks:
        flash('Please select at least one track to download', 'error')
        return redirect(url_for('search_youtube', session_id=session_id))
    
    # Create a temporary directory for MP3 downloads
    output_folder = tempfile.mkdtemp()
    
    # Download tracks using yt-dlp
    download_result = download_as_mp3(selected_tracks, output_folder)
    
    if not download_result['success']:
        flash('Error downloading tracks', 'error')
        return redirect(url_for('search_youtube', session_id=session_id))
    
    # Prepare results for the template
    download_results = []
    for i, url in enumerate(selected_tracks):
        # Find the corresponding downloaded file or error
        success = True
        title = f"Track {i+1}"
        error = None
        
        # Check if this URL was in failed downloads
        for failed in download_result['failed_downloads']:
            if failed['url'] == url:
                success = False
                error = failed['error']
                break
        
        # Find title if successful
        if success:
            for downloaded_file in download_result['downloaded_files']:
                # Extract basename for display
                basename = os.path.basename(downloaded_file)
                if basename:
                    title = basename
                    break
        
        download_results.append({
            "url": url,
            "title": title,
            "status": "success" if success else "error",
            "error": error
        })
    
    # Update session with download results
    sessions[session_id].update({
        'download_folder': download_result['download_folder'],
        'downloaded_files': download_result['downloaded_files'],
        'download_results': download_results
    })
    
    return render_template('download_complete.html', 
                          results=download_results, 
                          session_id=session_id)

@app.route('/downloads')
def list_downloads():
    """List all downloaded MP3 files"""
    # Get the latest session with downloads if available
    mp3_files = []
    download_folder = None
    
    for session_id, data in sessions.items():
        if 'downloaded_files' in data and data['downloaded_files']:
            download_folder = data['download_folder']
            for file_path in data['downloaded_files']:
                mp3_files.append(os.path.basename(file_path))
            break
    
    # If no session data, try to list files from a default downloads directory
    if not mp3_files and os.path.exists('downloads'):
        for file in os.listdir('downloads'):
            if file.endswith('.mp3'):
                mp3_files.append(file)
    
    return render_template('downloads.html', mp3_files=mp3_files, download_folder=download_folder)

@app.route('/download_file/<filename>')
def download_file(filename):
    """Download a specific MP3 file"""
    # Find the file in sessions
    file_path = None
    
    for session_id, data in sessions.items():
        if 'downloaded_files' in data:
            for path in data['downloaded_files']:
                if os.path.basename(path) == filename:
                    file_path = path
                    break
            if file_path:
                break
    
    # If not found in sessions, try default download directory
    if not file_path and os.path.exists(os.path.join('downloads', filename)):
        file_path = os.path.join('downloads', filename)
    
    if not file_path:
        flash('File not found', 'error')
        return redirect(url_for('list_downloads'))
    
    return send_file(file_path, as_attachment=True)

@app.route('/download_all/<session_id>')
def download_all(session_id):
    """Download all MP3 files as a ZIP archive"""
    if session_id not in sessions or 'download_folder' not in sessions[session_id]:
        flash('Session not found or no files available', 'error')
        return redirect(url_for('list_downloads'))
    
    folder_path = sessions[session_id]['download_folder']
    zip_file = create_zip_from_mp3s(folder_path)
    
    # Use playlist name for the zip file if available
    playlist_name = sessions[session_id].get('playlist_name', 'spotify_tracks')
    # Clean up playlist name for filename
    playlist_name = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in playlist_name)
    
    return send_file(
        zip_file, 
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{playlist_name}.zip'
    )

@app.route('/create_youtube_playlist/<session_id>', methods=['POST'])
def create_yt_playlist(session_id):
    """Create a YouTube playlist from selected tracks"""
    if session_id not in sessions:
        flash('Session expired or not found', 'error')
        return redirect(url_for('index'))
    
    selected_tracks = request.form.getlist('playlist_tracks')
    playlist_name = request.form.get('playlist_name', sessions[session_id].get('playlist_name', 'My Spotify Playlist'))
    
    if not selected_tracks:
        flash('Please select at least one track for the playlist', 'error')
        return redirect(url_for('search_youtube', session_id=session_id))
    
    # Extract just the video IDs
    video_ids = []
    for url in selected_tracks:
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            video_ids.append(video_id)
    
    # Call function to create playlist with OAuth
    result = create_youtube_playlist(video_ids, playlist_name)
    
    if result['success']:
        flash(f'Successfully created YouTube playlist: {playlist_name}', 'success')
        # Store playlist info in session
        sessions[session_id]['youtube_playlist'] = result
        return redirect(url_for('youtube_playlist_success', session_id=session_id))
    elif result.get('setup_required'):
        # OAuth setup is required
        flash('YouTube OAuth setup required. Please follow the instructions.', 'warning')
        return redirect(url_for('youtube_auth_setup', session_id=session_id))
    else:
        flash(f'Failed to create YouTube playlist: {result.get("error", "Unknown error")}', 'error')
        return redirect(url_for('search_youtube', session_id=session_id))

@app.route('/youtube_auth_setup/<session_id>')
def youtube_auth_setup(session_id):
    """Show instructions for setting up YouTube OAuth"""
    if session_id not in sessions:
        flash('Session expired or not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('youtube_auth_setup.html', session_id=session_id)

@app.route('/youtube_auth_callback')
def youtube_auth_callback():
    """Handle the OAuth callback from Google"""
    # This route will be called after user authorizes the application
    # Extract the session_id from state parameter if you implemented it
    session_id = request.args.get('state', '')
    
    if session_id and session_id in sessions:
        flash('YouTube authorization successful. You can now create playlists.', 'success')
        return redirect(url_for('search_youtube', session_id=session_id))
    else:
        flash('YouTube authorization process completed, but session was lost.', 'warning')
        return redirect(url_for('index'))

@app.route('/youtube_playlist_success/<session_id>')
def youtube_playlist_success(session_id):
    """Show success page after creating a YouTube playlist"""
    if session_id not in sessions or 'youtube_playlist' not in sessions[session_id]:
        flash('Session expired or playlist information not found', 'error')
        return redirect(url_for('index'))
    
    playlist_info = sessions[session_id]['youtube_playlist']
    return render_template('youtube_playlist_success.html', 
                          playlist=playlist_info,
                          session_id=session_id)

@app.route('/clear_downloads', methods=['POST'])
def clear_downloads():
    """Clear all downloaded files from the current session"""
    # This would normally delete files, but for safety just clear sessions
    sessions.clear()
    flash('All downloads cleared', 'success')
    return redirect(url_for('list_downloads'))

if __name__ == '__main__':
    app.run(debug=True)