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
    """Download media using social-media-downloader package"""
    try:
        from social_media_downloader import Downloader
        
        # Create downloads directory if it doesn't exist
        downloads_dir = 'downloads'
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Initialize the downloader
        downloader = Downloader()
        
        # Get media information
        info = downloader.get_info(url)
        
        if not info or not hasattr(info, 'download_url'):
            return {
                'success': False,
                'error': 'Could not extract media information from this URL'
            }
        
        media_url = info.download_url
        
        # Determine file extension and media type
        if hasattr(info, 'ext') and info.ext:
            file_ext = info.ext if info.ext.startswith('.') else f'.{info.ext}'
        else:
            # Try to determine from URL or default to mp4
            if any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                file_ext = '.jpg'
            else:
                file_ext = '.mp4'
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = str(hash(url))[-6:]
        
        if hasattr(info, 'title') and info.title:
            # Clean the title for filename
            clean_title = re.sub(r'[^\w\s-]', '', info.title)[:30]
            clean_title = re.sub(r'[-\s]+', '_', clean_title)
            filename = f"{platform}_{timestamp}_{clean_title}_{url_hash}{file_ext}"
        else:
            filename = f"{platform}_{timestamp}_{url_hash}{file_ext}"
        
        file_path = os.path.join(downloads_dir, filename)
        
        # Download the actual media file
        response = requests.get(media_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(file_path)
        
        # Determine media type
        media_type = 'image' if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif'] else 'video'
        
        return {
            'success': True,
            'filename': filename,
            'file_path': file_path,
            'file_size': file_size,
            'media_type': media_type,
            'title': getattr(info, 'title', None),
            'duration': getattr(info, 'duration', None)
        }
        
    except ImportError:
        return {
            'success': False,
            'error': 'Social media downloader package not properly installed'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to download media file: {str(e)}'
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
