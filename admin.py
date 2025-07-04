import os
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from sqlalchemy import func, desc, and_
from app import app, db
from utils import DownloadHistory, Blog, Image, LegalPage, ContactMessage, format_file_size
from app import db
from flask import send_file
import re
import uuid
from io import BytesIO
import mistune

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    # Basic statistics
    total_downloads = DownloadHistory.query.count()
    today_downloads = DownloadHistory.query.filter(
        func.date(DownloadHistory.created_at) == datetime.utcnow().date()
    ).count()
    
    # Platform statistics (simplified)
    platform_stats = db.session.query(
        DownloadHistory.platform,
        func.count(DownloadHistory.id).label('count')
    ).group_by(DownloadHistory.platform).limit(5).all()
    
    # Last 7 days stats (simplified)
    daily_stats = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = DownloadHistory.query.filter(
            func.date(DownloadHistory.created_at) == date
        ).count()
        daily_stats.append(type('obj', (object,), {
            'date': date,
            'downloads': count
        })())
    
    # Recent downloads (limited)
    recent_items = DownloadHistory.query.order_by(
        desc(DownloadHistory.created_at)
    ).limit(5).all()
    
    # Total storage
    total_storage = db.session.query(
        func.sum(DownloadHistory.file_size)
    ).scalar() or 0
    
    return render_template('admin/dashboard.html',
        total_downloads=total_downloads,
        today_downloads=today_downloads,
        platform_stats=platform_stats,
        daily_stats=daily_stats,
        recent_items=recent_items,
        total_storage=total_storage,
        format_file_size=format_file_size
    )

@app.route('/admin/downloads')
@admin_required
def admin_downloads():
    """Admin downloads management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    platform = request.args.get('platform', '')
    search = request.args.get('search', '')
    
    query = DownloadHistory.query
    
    # Apply filters
    if platform:
        query = query.filter(DownloadHistory.platform == platform)
    
    if search:
        query = query.filter(
            DownloadHistory.url.contains(search) |
            DownloadHistory.filename.contains(search)
        )
    
    # Paginate results
    downloads = query.order_by(desc(DownloadHistory.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get available platforms for filter
    platforms = db.session.query(DownloadHistory.platform).distinct().all()
    platforms = [p[0] for p in platforms]
    
    return render_template('admin/downloads.html',
        downloads=downloads,
        platforms=platforms,
        current_platform=platform,
        current_search=search,
        format_file_size=format_file_size
    )

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page"""
    # Hourly distribution
    hourly_stats_raw = db.session.query(
        func.extract('hour', DownloadHistory.created_at).label('hour'),
        func.count(DownloadHistory.id).label('count')
    ).group_by('hour').all()
    
    hourly_stats = [type('obj', (object,), {
        'hour': int(stat.hour) if stat.hour is not None else 0,
        'count': stat.count
    })() for stat in hourly_stats_raw]
    
    # Weekly distribution
    weekly_stats_raw = db.session.query(
        func.extract('dow', DownloadHistory.created_at).label('day_of_week'),
        func.count(DownloadHistory.id).label('count')
    ).group_by('day_of_week').all()
    
    weekly_stats = [type('obj', (object,), {
        'day_of_week': int(stat.day_of_week) if stat.day_of_week is not None else 0,
        'count': stat.count
    })() for stat in weekly_stats_raw]
    
    # Monthly trends (last 12 months)
    monthly_stats_raw = db.session.query(
        func.strftime('%Y-%m', DownloadHistory.created_at).label('month'),
        func.count(DownloadHistory.id).label('downloads'),
        func.sum(DownloadHistory.file_size).label('storage')
    ).filter(
        DownloadHistory.created_at >= datetime.utcnow() - timedelta(days=365)
    ).group_by('month').order_by('month').all()
    
    monthly_stats = [type('obj', (object,), {
        'month': stat.month,
        'downloads': stat.downloads,
        'storage': stat.storage or 0
    })() for stat in monthly_stats_raw]
    
    # Platform growth over time
    platform_growth_raw = db.session.query(
        func.date(DownloadHistory.created_at).label('date'),
        DownloadHistory.platform,
        func.count(DownloadHistory.id).label('count')
    ).filter(
        DownloadHistory.created_at >= datetime.utcnow() - timedelta(days=90)
    ).group_by('date', DownloadHistory.platform).order_by('date').all()
    
    platform_growth = []
    for stat in platform_growth_raw:
        if isinstance(stat.date, str):
            date_obj = datetime.strptime(stat.date, '%Y-%m-%d').date()
        else:
            date_obj = stat.date
        platform_growth.append(type('obj', (object,), {
            'date': date_obj,
            'platform': stat.platform,
            'count': stat.count
        })())
    
    return render_template('admin/analytics.html',
        hourly_stats=hourly_stats,
        weekly_stats=weekly_stats,
        monthly_stats=monthly_stats,
        platform_growth=platform_growth,
        format_file_size=format_file_size
    )

@app.route('/admin/api/stats')
@admin_required
def admin_api_stats():
    """API endpoint for real-time statistics"""
    # Get current statistics
    total_downloads = DownloadHistory.query.count()
    today_downloads = DownloadHistory.query.filter(
        func.date(DownloadHistory.created_at) == datetime.utcnow().date()
    ).count()
    
    total_storage = db.session.query(
        func.sum(DownloadHistory.file_size)
    ).scalar() or 0
    
    # Recent activity (last 24 hours)
    recent_activity_raw = db.session.query(
        func.strftime('%H:00', DownloadHistory.created_at).label('hour'),
        func.count(DownloadHistory.id).label('count')
    ).filter(
        DownloadHistory.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).group_by('hour').all()
    
    recent_activity = [type('obj', (object,), {
        'hour': stat.hour,
        'count': stat.count
    })() for stat in recent_activity_raw]
    
    return jsonify({
        'total_downloads': total_downloads,
        'today_downloads': today_downloads,
        'total_storage': total_storage,
        'total_storage_formatted': format_file_size(total_storage),
        'recent_activity': [{'hour': r.hour, 'count': r.count} for r in recent_activity]
    })

@app.route('/admin/api/delete-download/<int:download_id>', methods=['DELETE'])
@admin_required
def admin_delete_download(download_id):
    """Delete a download record and file"""
    try:
        download = DownloadHistory.query.get_or_404(download_id)
        
        # Delete file if it exists
        if download.file_path and os.path.exists(download.file_path):
            os.remove(download.file_path)
        
        # Delete from database
        db.session.delete(download)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Download deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/cleanup', methods=['POST'])
@admin_required
def admin_cleanup():
    """Clean up old files and records"""
    try:
        days = request.json.get('days', 7)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get records to delete
        old_records = DownloadHistory.query.filter(
            DownloadHistory.created_at < cutoff_date
        ).all()
        
        deleted_files = 0
        deleted_records = 0
        freed_space = 0
        
        for record in old_records:
            # Delete file if exists
            if record.file_path and os.path.exists(record.file_path):
                try:
                    file_size = os.path.getsize(record.file_path)
                    os.remove(record.file_path)
                    freed_space += file_size
                    deleted_files += 1
                except Exception:
                    pass
            
            # Delete record
            db.session.delete(record)
            deleted_records += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records,
            'freed_space': format_file_size(freed_space)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/blog')
@admin_required
def admin_blog():
    """Admin blog management"""
    blogs = Blog.query.order_by(desc(Blog.created_at)).all()
    return render_template('admin/blog.html', blogs=blogs)

@app.route('/admin/blog/new', methods=['GET', 'POST'])
@admin_required
def admin_blog_new():
    """Create new blog post"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        published = bool(request.form.get('published'))
        
        # Generate slug from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Process markdown to HTML with mistune
        html_content = mistune.html(content)
        
        # Handle thumbnail upload
        thumbnail_data = None
        thumbnail_mime_type = None
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename and thumbnail_file.content_type.startswith('image/'):
            thumbnail_data = thumbnail_file.read()
            thumbnail_mime_type = thumbnail_file.content_type
        
        thumbnail_style = request.form.get('thumbnail_style', 'cover')
        thumbnail_height = int(request.form.get('thumbnail_height', 192))
        
        blog = Blog(
            title=title,
            slug=slug,
            content=html_content,
            raw_content=content,
            excerpt=excerpt,
            thumbnail_data=thumbnail_data,
            thumbnail_mime_type=thumbnail_mime_type,
            thumbnail_style=thumbnail_style,
            thumbnail_height=thumbnail_height,
            published=published
        )
        db.session.add(blog)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin/blog_form.html')

@app.route('/admin/blog/edit/<int:blog_id>', methods=['GET', 'POST'])
@admin_required
def admin_blog_edit(blog_id):
    """Edit blog post"""
    blog = Blog.query.get_or_404(blog_id)
    
    if request.method == 'POST':
        content = request.form.get('content')
        # Process markdown to HTML with mistune
        html_content = mistune.html(content)
        
        blog.title = request.form.get('title')
        blog.content = html_content
        blog.raw_content = content
        blog.excerpt = request.form.get('excerpt')
        
        # Handle thumbnail upload
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename and thumbnail_file.content_type.startswith('image/'):
            blog.thumbnail_data = thumbnail_file.read()
            blog.thumbnail_mime_type = thumbnail_file.content_type
        
        blog.thumbnail_style = request.form.get('thumbnail_style', 'cover')
        blog.thumbnail_height = int(request.form.get('thumbnail_height', 192))
        
        blog.published = bool(request.form.get('published'))
        blog.updated_at = datetime.utcnow()
        
        # Update slug
        slug = re.sub(r'[^\w\s-]', '', blog.title.lower())
        blog.slug = re.sub(r'[-\s]+', '-', slug)
        
        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin/blog_form.html', blog=blog)

@app.route('/admin/api/toggle-blog/<int:blog_id>', methods=['POST'])
@admin_required
def admin_toggle_blog(blog_id):
    """Toggle blog publish status"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        blog.published = not blog.published
        db.session.commit()
        return jsonify({'success': True, 'published': blog.published})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/upload-image', methods=['POST'])
@admin_required
def admin_upload_image():
    """Upload image to database"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'File must be an image'}), 400
        
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Read file data
        file_data = file.read()
        
        # Create image record
        image = Image(
            filename=unique_filename,
            original_name=file.filename,
            file_size=len(file_data),
            mime_type=file.content_type,
            data=file_data
        )
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'url': f'/image/{unique_filename}',
            'markdown': f'![{file.filename}](/image/{unique_filename})'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/image/<filename>')
def serve_image(filename):
    """Serve image from database"""
    try:
        image = Image.query.filter_by(filename=filename).first_or_404()
        response = send_file(
            BytesIO(image.data),
            mimetype=image.mime_type,
            as_attachment=False
        )
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
    except Exception as e:
        return "Image not found", 404

@app.route('/blog-thumbnail/<int:blog_id>')
def serve_blog_thumbnail(blog_id):
    """Serve blog thumbnail from database"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        if not blog.thumbnail_data:
            return "No thumbnail", 404
        
        response = send_file(
            BytesIO(blog.thumbnail_data),
            mimetype=blog.thumbnail_mime_type,
            as_attachment=False
        )
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
    except Exception as e:
        return "Thumbnail not found", 404

@app.route('/admin/api/delete-blog/<int:blog_id>', methods=['DELETE'])
@admin_required
def admin_delete_blog(blog_id):
    """Delete blog post"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        db.session.delete(blog)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/legal')
@admin_required
def admin_legal():
    """Admin legal pages management"""
    # Ensure Privacy and Terms pages exist
    privacy = LegalPage.query.filter_by(slug='privacy-policy').first()
    if not privacy:
        privacy = LegalPage(
            title='Privacy Policy',
            slug='privacy-policy',
            content='<p>Privacy policy content goes here.</p>',
            raw_content='Privacy policy content goes here.',
            published=False
        )
        db.session.add(privacy)
    
    terms = LegalPage.query.filter_by(slug='terms-of-service').first()
    if not terms:
        terms = LegalPage(
            title='Terms of Service',
            slug='terms-of-service',
            content='<p>Terms of service content goes here.</p>',
            raw_content='Terms of service content goes here.',
            published=False
        )
        db.session.add(terms)
    
    db.session.commit()
    
    legal_pages = [privacy, terms]
    return render_template('admin/legal.html', legal_pages=legal_pages)

@app.route('/admin/legal/new', methods=['GET', 'POST'])
@admin_required
def admin_legal_new():
    """Create new legal page"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        excerpt = request.form.get('excerpt')
        published = bool(request.form.get('published'))
        
        # Generate slug from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Process markdown to HTML with mistune
        html_content = mistune.html(content)
        
        # Handle thumbnail upload
        thumbnail_data = None
        thumbnail_mime_type = None
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename and thumbnail_file.content_type.startswith('image/'):
            thumbnail_data = thumbnail_file.read()
            thumbnail_mime_type = thumbnail_file.content_type
        
        thumbnail_style = request.form.get('thumbnail_style', 'cover')
        thumbnail_height = int(request.form.get('thumbnail_height', 192))
        
        legal_page = LegalPage(
            title=title,
            slug=slug,
            content=html_content,
            raw_content=content,
            excerpt=excerpt,
            thumbnail_data=thumbnail_data,
            thumbnail_mime_type=thumbnail_mime_type,
            thumbnail_style=thumbnail_style,
            thumbnail_height=thumbnail_height,
            published=published
        )
        db.session.add(legal_page)
        db.session.commit()
        
        flash('Legal page created successfully!', 'success')
        return redirect(url_for('admin_legal'))
    
    return render_template('admin/legal_form.html')

@app.route('/admin/legal/edit/<int:legal_id>', methods=['GET', 'POST'])
@admin_required
def admin_legal_edit(legal_id):
    """Edit legal page"""
    legal_page = LegalPage.query.get_or_404(legal_id)
    
    if request.method == 'POST':
        content = request.form.get('content')
        # Process markdown to HTML with mistune
        html_content = mistune.html(content)
        
        legal_page.title = request.form.get('title')
        legal_page.content = html_content
        legal_page.raw_content = content
        legal_page.excerpt = request.form.get('excerpt')
        
        # Handle thumbnail upload
        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename and thumbnail_file.content_type.startswith('image/'):
            legal_page.thumbnail_data = thumbnail_file.read()
            legal_page.thumbnail_mime_type = thumbnail_file.content_type
        
        legal_page.thumbnail_style = request.form.get('thumbnail_style', 'cover')
        legal_page.thumbnail_height = int(request.form.get('thumbnail_height', 192))
        
        legal_page.published = bool(request.form.get('published'))
        legal_page.updated_at = datetime.utcnow()
        
        # Update slug
        slug = re.sub(r'[^\w\s-]', '', legal_page.title.lower())
        legal_page.slug = re.sub(r'[-\s]+', '-', slug)
        
        db.session.commit()
        flash('Legal page updated successfully!', 'success')
        return redirect(url_for('admin_legal'))
    
    return render_template('admin/legal_form.html', legal_page=legal_page)

@app.route('/admin/api/toggle-legal/<int:legal_id>', methods=['POST'])
@admin_required
def admin_toggle_legal(legal_id):
    """Toggle legal page publish status"""
    try:
        legal_page = LegalPage.query.get_or_404(legal_id)
        legal_page.published = not legal_page.published
        db.session.commit()
        return jsonify({'success': True, 'published': legal_page.published})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/delete-legal/<int:legal_id>', methods=['DELETE'])
@admin_required
def admin_delete_legal(legal_id):
    """Delete legal page"""
    try:
        legal_page = LegalPage.query.get_or_404(legal_id)
        db.session.delete(legal_page)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/legal-thumbnail/<int:legal_id>')
def serve_legal_thumbnail(legal_id):
    """Serve legal page thumbnail from database"""
    try:
        legal_page = LegalPage.query.get_or_404(legal_id)
        if not legal_page.thumbnail_data:
            return "No thumbnail", 404
        
        response = send_file(
            BytesIO(legal_page.thumbnail_data),
            mimetype=legal_page.thumbnail_mime_type,
            as_attachment=False
        )
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response
    except Exception as e:
        return "Thumbnail not found", 404

@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Admin messages management"""
    messages = ContactMessage.query.order_by(desc(ContactMessage.created_at)).all()
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/api/mark-read/<int:message_id>', methods=['POST'])
@admin_required
def admin_mark_read(message_id):
    """Mark message as read"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        message.read = not message.read
        db.session.commit()
        return jsonify({'success': True, 'read': message.read})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/delete-message/<int:message_id>', methods=['DELETE'])
@admin_required
def admin_delete_message(message_id):
    """Delete message"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings page"""
    # Get system information
    downloads_dir = 'downloads'
    total_files = 0
    total_size = 0
    
    if os.path.exists(downloads_dir):
        for filename in os.listdir(downloads_dir):
            if filename != '.gitkeep':
                file_path = os.path.join(downloads_dir, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
    
    # Database statistics
    db_stats = {
        'total_records': DownloadHistory.query.count(),
        'oldest_record': DownloadHistory.query.order_by(DownloadHistory.created_at).first(),
        'newest_record': DownloadHistory.query.order_by(desc(DownloadHistory.created_at)).first()
    }
    
    return render_template('admin/settings.html',
        total_files=total_files,
        total_size=format_file_size(total_size),
        db_stats=db_stats,
        format_file_size=format_file_size
    )