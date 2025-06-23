import os
import subprocess
from datetime import datetime

def download_media_with_format_debug(url, platform, format_id, download_type):
    """Debug version with prints"""
    try:
        import yt_dlp
        
        downloads_dir = 'downloads'
        os.makedirs(downloads_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"DEBUG: Starting download - type: {download_type}, platform: {platform}")
        
        if download_type == 'audio':
            print("DEBUG: Audio download path taken")
            
            # Download video first
            video_filename = f"{platform}_video_{timestamp}.mp4"
            video_path = os.path.join(downloads_dir, video_filename)
            print(f"DEBUG: Video will be saved to: {video_path}")
            
            ydl_opts = {'format': format_id, 'outtmpl': video_path}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            print(f"DEBUG: Video downloaded, exists: {os.path.exists(video_path)}")
            
            # Convert to MP3
            filename = f"{platform}_audio_{timestamp}.mp3"
            audio_path = os.path.join(downloads_dir, filename)
            
            cmd = ['ffmpeg', '-i', video_path, '-vn', '-ab', '192k', '-ar', '44100', '-y', audio_path]
            print(f"DEBUG: Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"DEBUG: FFmpeg return code: {result.returncode}")
            
            if result.returncode == 0:
                print(f"DEBUG: MP3 created successfully at {audio_path}")
                os.remove(video_path)
                return {'success': True, 'filename': filename, 'file_path': audio_path}
            else:
                print(f"DEBUG: FFmpeg failed: {result.stderr}")
                return {'success': False, 'error': result.stderr}
        else:
            print("DEBUG: Video download path taken")
            return {'success': False, 'error': 'Video download not implemented in debug'}
            
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        return {'success': False, 'error': str(e)}