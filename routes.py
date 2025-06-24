import os
import json
import tempfile
import threading
import time
import requests
from datetime import datetime
from urllib.parse import urlparse
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, Response
from app import app, db
from utils import (
    validate_url, 
    detect_platform, 
    download_media, 
    download_media_with_format,
    cleanup_old_files,
    get_file_info,
    DownloadHistory,
    Blog,
    Image
)
from utils_direct import get_direct_download_url

# Import admin routes
import admin

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    """Main page with download form"""
    return render_template('index.html')

@app.route('/history')
def history():
    """Download history page"""
    history_items = DownloadHistory.query.order_by(DownloadHistory.created_at.desc()).limit(50).all()
    return render_template('history.html', history=history_items)

@app.route('/validate-url', methods=['POST'])
def validate_url_route():
    """AJAX endpoint to validate URL and detect platform"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'valid': False, 'error': 'URL is required'})
    
    is_valid, error = validate_url(url)
    if not is_valid:
        return jsonify({'valid': False, 'error': error})
    
    platform = detect_platform(url)
    return jsonify({'valid': True, 'platform': platform})

@app.route('/get-video-info', methods=['POST'])
def get_video_info():
    """Get video information without downloading"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        platform = detect_platform(url)
        if not platform:
            return jsonify({'success': False, 'error': 'Unsupported platform'})
        
        # Get video info without downloading
        from utils import get_video_info
        info = get_video_info(url, platform)
        
        if info['success']:
            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'platform': platform,
                'file_size': info.get('file_size', 'Unknown')
            })
        else:
            return jsonify({'success': False, 'error': info.get('error', 'Failed to get video info')})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch video information'})

@app.route('/download', methods=['POST'])
def download():
    """Handle media download with quality selection"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        platform = data.get('platform', '').strip()
        format_id = data.get('format_id', '')
        download_type = data.get('type', 'video')
        
        print(f"DEBUG: Download request - type: {download_type}, format: {format_id}, platform: {platform}")
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Use server download for 'best' quality to ensure proper format merging
        if format_id and download_type == 'video' and format_id == 'best':
            result = download_media_with_format(url, platform, format_id, download_type)
        elif format_id and download_type == 'video':
            result = get_direct_download_url(url, platform, format_id, download_type)
            if result['success']:
                if result.get('youtube_proxy'):
                    return jsonify({
                        'success': True,
                        'youtube_proxy': True,
                        'proxy_url': f'/youtube-proxy?url={result["download_url"]}&filename={result["filename"]}',
                        'filename': result['filename'],
                        'message': 'YouTube download ready'
                    })
                else:
                    return jsonify({
                        'success': True,
                        'direct_download': True,
                        'download_url': result['download_url'],
                        'filename': result['filename'],
                        'message': 'Direct download link ready'
                    })
        elif format_id:
            result = download_media_with_format(url, platform, format_id, download_type)
        else:
            result = download_media(url, platform)
        
        if result['success']:
            # Save to history for server downloads
            history_item = DownloadHistory(
                url=url,
                platform=platform,
                filename=result['filename'],
                file_path=result['file_path'],
                file_size=result['file_size'],
                media_type=result.get('media_type', download_type)
            )
            db.session.add(history_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'filename': result['filename'],
                'file_size': result.get('file_size', 0),
                'media_type': result.get('media_type', download_type),
                'download_url': url_for('download_file', filename=result['filename']),
                'message': f'{download_type.title()} downloaded successfully!'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'})

@app.route('/youtube-proxy')
def youtube_proxy():
    """Proxy YouTube video downloads"""
    try:
        video_url = request.args.get('url')
        filename = request.args.get('filename', 'video.mp4')
        
        if not video_url:
            return "No URL provided", 400
        
        # Get video with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        def generate():
            try:
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        yield chunk
            except Exception as e:
                print(f"Streaming error: {e}")
        
        return Response(
            generate(),
            content_type='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': response.headers.get('Content-Length', ''),
                'Accept-Ranges': 'bytes'
            }
        )
        
    except Exception as e:
        print(f"Proxy error: {e}")
        return f"Download failed: {str(e)}", 500

@app.route('/download-file/<filename>')
def download_file(filename):
    """Serve downloaded file and delete after 45 seconds"""
    file_path = os.path.join('downloads', filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    def cleanup_after_delay():
        try:
            os.remove(file_path)
            history_item = DownloadHistory.query.filter_by(filename=filename).first()
            if history_item:
                db.session.delete(history_item)
                db.session.commit()
        except Exception:
            pass
    
    threading.Timer(20.0, cleanup_after_delay).start()
    return send_file(file_path, as_attachment=True)

@app.route('/delete-history/<int:item_id>', methods=['POST'])
def delete_history_item(item_id):
    """Delete history item"""
    try:
        item = DownloadHistory.query.get_or_404(item_id)
        
        # Delete file if it exists
        if item.file_path and os.path.exists(item.file_path):
            os.remove(item.file_path)
        
        # Delete from database
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Delete history error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete item'})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.route('/blog')
def blog_list():
    """Blog listing page"""
    print("=== BLOG ROUTE ACCESSED ===")
    try:
        blogs = Blog.query.all()
        print(f"Found {len(blogs)} total blogs")
        published = [b for b in blogs if b.published]
        print(f"Found {len(published)} published blogs")
        return render_template('blog/list.html', blogs=published)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('blog/list.html', blogs=[])

@app.route('/blog/<slug>')
def blog_detail(slug):
    """Blog detail page"""
    blog = Blog.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template('blog/detail.html', blog=blog)

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html'), 500