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
            'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'
        ]
        
        domain = parsed.netloc.lower()
        if not any(supported_domain in domain for supported_domain in supported_domains):
            return False, "URL must be from Instagram, TikTok, Facebook, Twitter/X, or YouTube"
        
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
