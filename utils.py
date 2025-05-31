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
            'twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'
        ]
        
        domain = parsed.netloc.lower()
        if not any(supported_domain in domain for supported_domain in supported_domains):
            return False, "URL must be from Instagram, TikTok, Facebook, or Twitter/X"
        
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
        
        return None
        
    except Exception:
        return None

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
