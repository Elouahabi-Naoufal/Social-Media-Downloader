import os
import re
import tempfile
import threading
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlparse
from app import db
from sqlalchemy import Column, Integer, String, DateTime, BigInteger

class DownloadHistory(db.Model):
    """Model for storing download history"""
    __tablename__ = 'download_history'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    media_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

class Blog(db.Model):
    """Model for blog posts"""
    __tablename__ = 'blogs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True)
    content = Column(db.Text, nullable=False)  # Processed HTML
    raw_content = Column(db.Text, nullable=False)  # Original markdown
    excerpt = Column(String(300))
    thumbnail_data = Column(db.LargeBinary)
    thumbnail_mime_type = Column(String(100))
    thumbnail_style = Column(String(20), default='cover')
    thumbnail_height = Column(Integer, default=192)
    published = Column(db.Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Image(db.Model):
    """Model for uploaded images"""
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    data = Column(db.LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class LegalPage(db.Model):
    """Model for legal pages"""
    __tablename__ = 'legal_pages'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True)
    content = Column(db.Text, nullable=False)  # Processed HTML
    raw_content = Column(db.Text, nullable=False)  # Original markdown
    excerpt = Column(String(300))
    thumbnail_data = Column(db.LargeBinary)
    thumbnail_mime_type = Column(String(100))
    thumbnail_style = Column(String(20), default='cover')
    thumbnail_height = Column(Integer, default=192)
    published = Column(db.Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactMessage(db.Model):
    """Model for contact messages"""
    __tablename__ = 'contact_messages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    message = Column(db.Text, nullable=False)
    read = Column(db.Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def validate_url(url):
    """Validate if URL is properly formatted and accessible"""
    try:
        # Basic URL format validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"
        
        # Check if URL is from supported platforms
        supported_domains = [
            'instagram.com', 'www.instagram.com',
            'tiktok.com', 'www.tiktok.com', 'vm.tiktok.com',
            'facebook.com', 'www.facebook.com', 'fb.watch',
            'twitter.com', 'www.twitter.com', 'x.com', 'www.x.com',
            'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com',
            'reddit.com', 'www.reddit.com', 'old.reddit.com'
        ]
        
        domain = parsed.netloc.lower()
        if not any(supported_domain in domain for supported_domain in supported_domains):
            return False, "URL must be from Instagram, TikTok, Facebook, Twitter/X, YouTube, or Reddit"
        
        return True, None
        
    except Exception as e:
        return False, f"URL validation error: {str(e)}"

def detect_platform(url):
    """Auto-detect platform from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'instagram.com' in domain:
            return 'instagram'
        elif 'tiktok.com' in domain:
            return 'tiktok'
        elif 'facebook.com' in domain or 'fb.watch' in domain:
            return 'facebook'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'reddit.com' in domain:
            return 'reddit'

        
        return None
        
    except Exception:
        return None

def get_available_formats(url):
    """Get simplified quality options (Best, Medium, Low)"""
    try:
        # Simple quality options using yt-dlp format words
        video_formats = [
            {'format_id': 'best', 'quality': 'Best', 'type': 'video'},
            {'format_id': 'worst[height>=480]', 'quality': 'Medium', 'type': 'video'},
            {'format_id': 'worst', 'quality': 'Low', 'type': 'video'}
        ]
        
        audio_formats = [
            {'format_id': 'bestaudio', 'quality': 'Best', 'type': 'audio'},
            {'format_id': 'bestaudio[abr>=96]', 'quality': 'Medium', 'type': 'audio'},
            {'format_id': 'worstaudio', 'quality': 'Low', 'type': 'audio'}
        ]
        
        return {
            'success': True,
            'video_formats': video_formats,
            'audio_formats': audio_formats
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_video_info(url, platform):
    """Get video information without downloading"""
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration')
            if duration:
                duration = int(duration)  # Convert float to int
                duration_str = f"{duration//60}:{duration%60:02d}"
            else:
                duration_str = 'Unknown'
            
            # Get file size from best format
            file_size = 'Unknown'
            if info.get('formats'):
                # For Instagram, try video-only formats first as they often have size info
                formats_to_check = info['formats']
                if platform == 'instagram':
                    # Check video-only formats first for Instagram
                    video_formats = [f for f in formats_to_check if f.get('vcodec') != 'none' and f.get('acodec') == 'none']
                    audio_formats = [f for f in formats_to_check if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    combined_formats = [f for f in formats_to_check if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                    formats_to_check = combined_formats + video_formats + audio_formats
                
                for fmt in formats_to_check:
                    # Try different size fields
                    size = fmt.get('filesize') or fmt.get('filesize_approx') or fmt.get('http_headers', {}).get('Content-Length')
                    if size:
                        file_size = format_file_size(int(size))
                        break
                    # Estimate from bitrate and duration
                    elif fmt.get('tbr') and duration:
                        estimated_size = int(fmt['tbr'] * 1000 * duration / 8)
                        file_size = f"~{format_file_size(estimated_size)}"
                        break
            
            # Fix Instagram thumbnail by downloading it server-side
            thumbnail = info.get('thumbnail', '')
            if platform == 'instagram' and thumbnail:
                try:
                    import requests
                    import hashlib
                    # Create unique filename
                    thumb_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    thumb_filename = f"thumb_{thumb_hash}.jpg"
                    thumb_path = os.path.join('static', 'thumbnails', thumb_filename)
                    
                    # Create directory
                    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                    
                    # Download thumbnail
                    if not os.path.exists(thumb_path):
                        response = requests.get(thumbnail, timeout=10)
                        if response.status_code == 200:
                            with open(thumb_path, 'wb') as f:
                                f.write(response.content)
                    
                    thumbnail = f'/static/thumbnails/{thumb_filename}'
                except:
                    thumbnail = ''
            
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': duration_str,
                'thumbnail': thumbnail,
                'file_size': file_size
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

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

def download_media(url, platform):
    """Download media using yt-dlp"""
    try:
        import yt_dlp
        
        # Create downloads directory if it doesn't exist
        downloads_dir = 'downloads'
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Generate base filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = str(hash(url))[-6:]
        base_filename = f"{platform}_{timestamp}_{url_hash}"
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': os.path.join(downloads_dir, f'{base_filename}.%(ext)s'),
            'format': 'best[height<=720]/best',  # Download best quality up to 720p
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extractaudio': False,
            'audioformat': 'mp3',
            'audioquality': '192',
        }
        
        # Extract information first
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Could not extract media information: {str(e)}'
                }
        
        if not info:
            return {
                'success': False,
                'error': 'No media information found for this URL'
            }
        
        # Get media details
        title = info.get('title', 'Unknown')
        duration = info.get('duration')
        ext = info.get('ext', 'mp4')
        
        # Clean title for filename
        clean_title = re.sub(r'[^\w\s-]', '', title)[:30]
        clean_title = re.sub(r'[-\s]+', '_', clean_title)
        
        # Update filename with clean title
        final_filename = f"{platform}_{timestamp}_{clean_title}_{url_hash}.{ext}"
        ydl_opts['outtmpl'] = os.path.join(downloads_dir, final_filename)
        
        # Download the media
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Download failed: {str(e)}'
                }
        
        file_path = os.path.join(downloads_dir, final_filename)
        
        # Check if file was downloaded
        if not os.path.exists(file_path):
            # Sometimes yt-dlp changes the extension, look for any file with our base name
            for file in os.listdir(downloads_dir):
                if file.startswith(f"{platform}_{timestamp}_{clean_title}_{url_hash}"):
                    file_path = os.path.join(downloads_dir, file)
                    final_filename = file
                    break
            else:
                return {
                    'success': False,
                    'error': 'Download completed but file not found'
                }
        
        file_size = os.path.getsize(file_path)
        
        # Determine media type based on file extension
        video_extensions = ['.mp4', '.avi', '.mkv', '.webm', '.mov', '.flv', '.wmv']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        file_ext = os.path.splitext(final_filename)[1].lower()
        if file_ext in video_extensions:
            media_type = 'video'
        elif file_ext in image_extensions:
            media_type = 'image'
        else:
            media_type = 'video'  # Default to video
        
        return {
            'success': True,
            'filename': final_filename,
            'file_path': file_path,
            'file_size': file_size,
            'media_type': media_type,
            'title': title,
            'duration': duration
        }
        
    except ImportError:
        return {
            'success': False,
            'error': 'Media downloader not available. Please contact support.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Download failed: {str(e)}'
        }

def get_file_info(file_path):
    """Get file information"""
    try:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime)
            }
        return None
    except Exception:
        return None

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def cleanup_old_files():
    """Background task to cleanup old downloaded files"""
    while True:
        try:
            # Sleep for 1 hour between cleanups
            time.sleep(3600)
            
            # Remove files older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean up files from filesystem
            downloads_dir = 'downloads'
            if os.path.exists(downloads_dir):
                for filename in os.listdir(downloads_dir):
                    if filename == '.gitkeep':
                        continue
                        
                    file_path = os.path.join(downloads_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < cutoff_time:
                                os.remove(file_path)
                    except Exception as e:
                        print(f"Error cleaning up file {file_path}: {e}")
            
            # Clean up database records for non-existent files
            with db.app.app_context():
                history_items = DownloadHistory.query.filter(
                    DownloadHistory.created_at < cutoff_time
                ).all()
                
                for item in history_items:
                    try:
                        if item.file_path and os.path.exists(item.file_path):
                            os.remove(item.file_path)
                    except Exception:
                        pass
                    
                    db.session.delete(item)
                
                db.session.commit()
                
        except Exception as e:
            print(f"Cleanup error: {e}")