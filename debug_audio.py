#!/usr/bin/env python3

import subprocess
import os

# Test ffmpeg conversion directly
video_file = "downloads/instagram_20250623_123319_Video_by_hichem_keniche_252540.mp4"
audio_file = "downloads/test_audio.mp3"

if os.path.exists(video_file):
    print(f"Video file exists: {video_file}")
    
    cmd = ['ffmpeg', '-i', video_file, '-vn', '-ab', '192k', '-ar', '44100', '-y', audio_file]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    print(f"Stderr: {result.stderr}")
    print(f"Stdout: {result.stdout}")
    
    if os.path.exists(audio_file):
        print(f"SUCCESS: MP3 created at {audio_file}")
        print(f"File size: {os.path.getsize(audio_file)} bytes")
    else:
        print("FAILED: MP3 not created")
else:
    print(f"Video file not found: {video_file}")
    print("Available files in downloads:")
    if os.path.exists("downloads"):
        for f in os.listdir("downloads"):
            print(f"  {f}")