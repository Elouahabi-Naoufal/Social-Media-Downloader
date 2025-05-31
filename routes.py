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
    cleanup_old_files,
    get_file_info,
    DownloadHistory
)

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

@app.route('/download', methods=['POST'])
def download():
    """Handle media download"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        platform = data.get('platform', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Validate URL
        is_valid, error = validate_url(url)
        if not is_valid:
            return jsonify({'success': False, 'error': error})
        
        # Auto-detect platform if not provided
        if not platform:
            platform = detect_platform(url)
        
        if not platform:
            return jsonify({'success': False, 'error': 'Could not detect platform. Please select manually.'})
        
        # Download media
        result = download_media(url, platform)
        
        if result['success']:
            # Save to history
            history_item = DownloadHistory(
                url=url,
                platform=platform,
                filename=result['filename'],
                file_path=result['file_path'],
                file_size=result['file_size'],
                media_type=result['media_type']
            )
            db.session.add(history_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'filename': result['filename'],
                'file_size': result['file_size'],
                'media_type': result['media_type'],
                'download_url': url_for('download_file', filename=result['filename'])
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

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('index.html'), 500
