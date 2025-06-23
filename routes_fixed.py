import os
import json
import tempfile
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file
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
        
        print(f"DEBUG: Download request - type: {download_type}, format: {format_id}")
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Use format-specific download if format_id provided
        if format_id:
            result = download_media_with_format(url, platform, format_id, download_type)
        else:
            result = download_media(url, platform)
        
        if result['success']:
            # Save to history
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
                'file_size': result['file_size'],
                'media_type': result.get('media_type', download_type),
                'download_url': url_for('download_file', filename=result['filename']),
                'message': f'{download_type.title()} downloaded to server. Click the download link to save to your device.'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'})

@app.route('/download-file/<filename>')
def download_file(filename):
    """Serve downloaded file"""
    try:
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash('File not found or has been cleaned up', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"File download error: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('index'))

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