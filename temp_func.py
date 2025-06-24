def download_media_with_format(url, platform, format_id, download_type):
    """Download media with specific format selection"""
    try:
        import yt_dlp
        import subprocess
        import os
        from datetime import datetime
        
        # Create downloads directory
        downloads_dir = 'downloads'
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if download_type == 'audio':
            print(f"DEBUG: Audio download started")
            
            # First download video using 'best' format
            video_filename = f"{platform}_video_{timestamp}.mp4"
            video_path = os.path.join(downloads_dir, video_filename)
            
            ydl_opts_video = {
                'format': 'best',
                'outtmpl': video_path
            }
            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                ydl.download([url])
            
            print(f"DEBUG: Video downloaded, exists: {os.path.exists(video_path)}")
            
            # Convert to MP3 using ffmpeg
            filename = f"{platform}_audio_{timestamp}.mp3"
            audio_path = os.path.join(downloads_dir, filename)
            
            cmd = ['ffmpeg', '-i', video_path, '-vn', '-ab', '192k', '-ar', '44100', '-y', audio_path]
            print(f"DEBUG: Running ffmpeg: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(f"DEBUG: FFmpeg return code: {result.returncode}")
            
            if result.returncode != 0:
                print(f"DEBUG: FFmpeg failed: {result.stderr}")
                return {'success': False, 'error': f'FFmpeg failed: {result.stderr}'}
            
            print(f"DEBUG: MP3 created, exists: {os.path.exists(audio_path)}")
            
            # Remove video file
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"DEBUG: Removed video file")
        else:
            filename = f"{platform}_video_{timestamp}.mp4"
            
            # Use highest quality available for 'best' quality
            if format_id == 'best':
                format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
                merge_format = 'mp4'
            else:
                format_selector = format_id
                merge_format = None
                
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(downloads_dir, filename)
            }
            
            if merge_format:
                ydl_opts['merge_output_format'] = merge_format
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        
        file_path = os.path.join(downloads_dir, filename)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return {
            'success': True,
            'filename': filename,
            'file_path': file_path,
            'file_size': file_size,
            'media_type': download_type
        }
    except Exception as e:
        print(f"DEBUG: Exception in download_media_with_format: {str(e)}")
        return {'success': False, 'error': str(e)}