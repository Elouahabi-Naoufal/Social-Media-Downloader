#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
import yt_dlp

def test_audio_download():
    url = "https://www.instagram.com/reels/C_D_i9HoDC8/"
    platform = "instagram"
    format_id = "best"  # Use 'best' instead of audio-specific format
    
    downloads_dir = 'downloads'
    os.makedirs(downloads_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("DEBUG: Starting audio download test")
    
    # Download video first
    video_filename = f"{platform}_video_{timestamp}.mp4"
    video_path = os.path.join(downloads_dir, video_filename)
    print(f"DEBUG: Video path: {video_path}")
    
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
        print(f"SUCCESS: MP3 created at {audio_path}")
        print(f"File size: {os.path.getsize(audio_path)} bytes")
        os.remove(video_path)
    else:
        print(f"FAILED: {result.stderr}")

if __name__ == "__main__":
    test_audio_download()