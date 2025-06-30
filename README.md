# Social Media Downloader

A powerful web application for downloading media content from popular social media platforms including Instagram, TikTok, Facebook, Twitter/X, YouTube, and Reddit.

## 🚀 Features

### Core Functionality
- **Multi-Platform Support**: Download from Instagram, TikTok, Facebook, Twitter/X, YouTube, and Reddit
- **Multiple Quality Options**: Choose from Best, Medium, or Low quality for videos
- **Audio Extraction**: Download audio-only versions of videos in MP3 format
- **Direct Downloads**: Get direct download links for supported platforms
- **Download History**: Track all your downloads with timestamps and file information
- **Auto Cleanup**: Automatic cleanup of old files to save storage space

### Admin Panel
- **Dashboard**: Real-time statistics and analytics
- **Download Management**: View, search, and manage all downloads
- **Blog System**: Create and manage blog posts with markdown support
- **Legal Pages**: Manage privacy policy and terms of service
- **Contact Messages**: Handle user inquiries
- **System Settings**: Monitor storage usage and system health

### Technical Features
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: JSON-based API for all operations
- **Database Storage**: SQLite database for data persistence
- **File Management**: Automatic file cleanup and storage optimization
- **Security**: Admin authentication and session management

## 🛠️ Technologies Used

### Backend Technologies
- **Python 3.11+** - Core programming language
- **Flask 3.1.1** - Web framework for the application
- **SQLAlchemy 2.0.41** - Database ORM for data management
- **SQLite** - Default database (can be changed to PostgreSQL)
- **yt-dlp 2025.5.22** - Media extraction and downloading engine
- **FFmpeg** - Audio/video processing and conversion
- **Gunicorn** - WSGI HTTP Server for production deployment

### Frontend Technologies
- **HTML5** - Markup structure
- **CSS3** - Styling and responsive design
- **JavaScript (Vanilla)** - Client-side interactivity
- **Bootstrap-like responsive design** - Mobile-first approach

### Additional Libraries
- **Requests** - HTTP library for API calls
- **Werkzeug** - WSGI utilities and security
- **Mistune** - Markdown processing for blog content
- **Email-validator** - Email validation utilities

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.11 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 2GB free space (more for downloads)
- **Network**: Stable internet connection

### Required Software
1. **Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **FFmpeg** (Essential for audio conversion)
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - **CentOS/RHEL**: `sudo yum install ffmpeg` or `sudo dnf install ffmpeg`
   - **macOS**: `brew install ffmpeg` (requires Homebrew)
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Verify installation: `ffmpeg -version`

3. **Git** (for cloning repository)
   - Most systems have it pre-installed
   - Download from [git-scm.com](https://git-scm.com/) if needed

## 🚀 Installation Guide

### Step 1: Prepare Your System

**Check Python Version:**
```bash
python --version  # Should be 3.11 or higher
# If not available, try:
python3 --version
```

**Install FFmpeg:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS (with Homebrew)
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### Step 2: Download the Application

**Option A: Clone with Git**
```bash
git clone <your-repository-url>
cd SocialMediaDownloader
```

**Option B: Download ZIP**
- Download the ZIP file from your repository
- Extract to your desired location
- Navigate to the extracted folder

### Step 3: Set Up Python Environment

**Create Virtual Environment:**
```bash
# Using venv (recommended)
python -m venv env

# On some systems, use python3
python3 -m venv env
```

**Activate Virtual Environment:**
```bash
# Linux/macOS
source env/bin/activate

# Windows Command Prompt
env\Scripts\activate

# Windows PowerShell
env\Scripts\Activate.ps1
```

**Verify Activation:**
Your terminal prompt should show `(env)` at the beginning.

### Step 4: Install Dependencies

**Upgrade pip first:**
```bash
pip install --upgrade pip
```

**Install application dependencies:**
```bash
# Option 1: Using requirements.txt (recommended)
pip install -r requirements.txt

# Option 2: Using pyproject.toml
pip install -e .
```

**Verify Installation:**
```bash
pip list  # Should show all installed packages
```

### Step 5: Configure the Application

**Create Environment File (Optional but Recommended):**
```bash
# Create .env file
touch .env  # Linux/macOS
# On Windows, create the file manually
```

**Add Configuration to .env:**
```bash
# Admin Panel Credentials (CHANGE THESE!)
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password_123

# Session Security (CHANGE THIS!)
SESSION_SECRET=your_random_secret_key_here

# Database Configuration
DATABASE_URL=sqlite:///downloads.db

# Application Environment
FLASK_ENV=production
```

**Set Permissions (Linux/macOS):**
```bash
chmod 600 .env  # Restrict access to environment file
mkdir -p downloads static/thumbnails instance
```

### Step 6: Initialize the Database

**Run the application once to create database:**
```bash
python app.py
```

The application will:
- Create the SQLite database automatically
- Set up all required tables
- Create necessary directories
- Start the web server

**You should see:**
```
* Running on http://127.0.0.1:5000
* Debug mode: off
```

## 🚀 Running the Application

### Development Mode (Testing)
```bash
# Make sure virtual environment is activated
source env/bin/activate  # Linux/macOS
# or env\Scripts\activate  # Windows

# Run the application
python app.py
```

**Access Points:**
- **Main Application**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- **Download History**: http://localhost:5000/history
- **Blog**: http://localhost:5000/blog

### Production Mode (Live Server)

**Using Gunicorn (Linux/macOS):**
```bash
# Basic production setup
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With more options
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 2 app:app
```

**Using Waitress (Windows):**
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### First-Time Setup

1. **Start the application**
2. **Visit**: http://localhost:5000
3. **Test a download** with any supported social media URL
4. **Access admin panel**: http://localhost:5000/admin
   - Default credentials: admin/admin123 (CHANGE THESE!)
5. **Configure admin settings** and change passwords

## 📖 Usage Guide

### Basic Download Process

1. **Visit the Homepage**: Navigate to `http://localhost:5000`
2. **Enter URL**: Paste the social media URL in the input field
3. **Select Quality**: Choose video quality (Best/Medium/Low) or audio-only
4. **Download**: Click download and wait for processing
5. **Get File**: Download the processed file or use the direct link

### Supported URL Formats

**Instagram:**
- Posts: `https://www.instagram.com/p/[POST_ID]/`
- Reels: `https://www.instagram.com/reel/[REEL_ID]/`

**TikTok:**
- Videos: `https://www.tiktok.com/@[USERNAME]/video/[VIDEO_ID]`
- Short URLs: `https://vm.tiktok.com/[SHORT_ID]`

**YouTube:**
- Videos: `https://www.youtube.com/watch?v=[VIDEO_ID]`
- Shorts: `https://www.youtube.com/shorts/[VIDEO_ID]`
- Short URLs: `https://youtu.be/[VIDEO_ID]`

**Twitter/X:**
- Tweets: `https://twitter.com/[USERNAME]/status/[TWEET_ID]`
- X URLs: `https://x.com/[USERNAME]/status/[TWEET_ID]`

**Facebook:**
- Videos: `https://www.facebook.com/[USERNAME]/videos/[VIDEO_ID]`
- Watch URLs: `https://fb.watch/[VIDEO_ID]`

**Reddit:**
- Posts: `https://www.reddit.com/r/[SUBREDDIT]/comments/[POST_ID]/`

### Download History

- Access your download history at `/history`
- View file details, download dates, and file sizes
- Delete individual items from history
- Files are automatically cleaned up after 24 hours

## 🔧 Admin Panel

### Accessing Admin Panel

1. Navigate to `/admin/login`
2. Enter admin credentials (default: admin/admin123)
3. Access the dashboard at `/admin`

### Admin Features

#### Dashboard (`/admin`)
- Total downloads statistics
- Daily/weekly/monthly trends
- Platform usage statistics
- Recent download activity
- Storage usage monitoring

#### Downloads Management (`/admin/downloads`)
- View all downloads with pagination
- Filter by platform or search by URL/filename
- Delete individual downloads
- Bulk cleanup operations

#### Blog Management (`/admin/blog`)
- Create new blog posts with markdown
- Upload and manage images
- Set featured thumbnails
- Publish/unpublish posts
- SEO-friendly URLs

#### Legal Pages (`/admin/legal`)
- Manage Privacy Policy
- Manage Terms of Service
- Create additional legal pages
- Markdown support with live preview

#### Messages (`/admin/messages`)
- View contact form submissions
- Mark messages as read/unread
- Delete messages
- Respond to user inquiries

#### Settings (`/admin/settings`)
- System information
- Storage usage statistics
- Database statistics
- Cleanup operations

### Admin API Endpoints

- `GET /admin/api/stats` - Real-time statistics
- `DELETE /admin/api/delete-download/<id>` - Delete download
- `POST /admin/api/cleanup` - Cleanup old files
- `POST /admin/api/toggle-blog/<id>` - Toggle blog status
- `POST /admin/api/upload-image` - Upload images

## 🗂️ File Structure

```
SocialMediaDownloader/
├── app.py              # Flask application setup
├── routes.py           # Main application routes
├── admin.py            # Admin panel routes
├── utils.py            # Utility functions and models
├── pyproject.toml      # Project dependencies
├── downloads.db        # SQLite database
├── downloads/          # Downloaded files (auto-cleanup)
├── static/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── thumbnails/    # Video thumbnails
├── templates/
│   ├── admin/         # Admin panel templates
│   ├── blog/          # Blog templates
│   ├── legal/         # Legal page templates
│   ├── base.html      # Base template
│   ├── index.html     # Homepage
│   ├── history.html   # Download history
│   └── contact.html   # Contact form
└── instance/
    └── downloads.db   # Database instance
```

## 🔒 Security Considerations

### Admin Security
- Change default admin credentials immediately
- Use strong passwords
- Set secure session secrets
- Enable HTTPS in production

### File Security
- Files are automatically cleaned up after 24 hours
- Download directory is not web-accessible
- File size limits prevent abuse

### Database Security
- SQLite database with proper permissions
- SQL injection protection via SQLAlchemy ORM
- Input validation on all forms

## 🚀 Deployment

### Using Gunicorn (Recommended)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install -e .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Production Environment Setup

**Create Production .env file:**
```bash
# Security Settings (CRITICAL - CHANGE ALL OF THESE!)
ADMIN_USERNAME=your_secure_admin_username
ADMIN_PASSWORD=your_very_secure_password_123!
SESSION_SECRET=your_random_64_character_secret_key_here_change_this

# Database (for production, consider PostgreSQL)
DATABASE_URL=sqlite:///instance/downloads.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=False

# Optional: External service configurations
# SENTRY_DSN=your_sentry_dsn_for_error_tracking
```

**Set Environment Variables (Alternative to .env):**
```bash
export ADMIN_USERNAME="your_secure_admin"
export ADMIN_PASSWORD="your_secure_password_123!"
export SESSION_SECRET="your_64_char_secret_key"
export DATABASE_URL="sqlite:///instance/downloads.db"
export FLASK_ENV="production"
```

## 🔧 Troubleshooting

### Installation Issues

**Python Version Problems:**
```bash
# Check your Python version
python --version
python3 --version

# If Python 3.11+ is not available:
# Ubuntu/Debian: sudo apt install python3.11
# macOS: brew install python@3.11
# Windows: Download from python.org
```

**Virtual Environment Issues:**
```bash
# If venv module is missing:
pip install virtualenv
virtualenv env

# Alternative virtual environment creation:
python -m pip install virtualenv
python -m virtualenv env
```

**FFmpeg Installation Problems:**
```bash
# Test FFmpeg installation
ffmpeg -version

# If command not found:
# Ubuntu/Debian: sudo apt install ffmpeg
# CentOS: sudo yum install epel-release && sudo yum install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from ffmpeg.org and add to PATH

# Verify PATH (Windows)
echo %PATH%
# Verify PATH (Linux/macOS)
echo $PATH
```

**Dependency Installation Failures:**
```bash
# Update pip first
pip install --upgrade pip setuptools wheel

# If specific packages fail:
pip install --upgrade --force-reinstall package_name

# For compilation errors (Linux):
sudo apt install python3-dev build-essential

# For macOS compilation errors:
xcode-select --install
```

### Runtime Issues

**Application Won't Start:**
```bash
# Check if virtual environment is activated
which python  # Should point to env/bin/python

# Check if all dependencies are installed
pip list | grep flask
pip list | grep yt-dlp

# Run with verbose output
python -v app.py
```

**Database Errors:**
```bash
# Check file permissions
ls -la downloads.db
ls -la instance/

# Recreate database if corrupted
rm downloads.db instance/downloads.db
python app.py  # Will recreate automatically
```

**Download Failures:**
```bash
# Test yt-dlp directly
yt-dlp --version
yt-dlp "https://www.youtube.com/watch?v=test_url"

# Check internet connectivity
ping google.com
curl -I https://www.instagram.com

# Update yt-dlp
pip install --upgrade yt-dlp
```

**FFmpeg Audio Conversion Issues:**
```bash
# Test FFmpeg directly
ffmpeg -f lavfi -i testsrc2=duration=1:size=320x240:rate=1 test.mp4
ffmpeg -i test.mp4 -vn -ab 192k test.mp3

# Check FFmpeg codecs
ffmpeg -codecs | grep mp3
ffmpeg -codecs | grep aac
```

**Admin Panel Access Issues:**
```bash
# Check if admin credentials are set
echo $ADMIN_USERNAME
echo $ADMIN_PASSWORD

# Clear browser cache and cookies
# Try incognito/private browsing mode

# Check session secret
echo $SESSION_SECRET
```

**Port Already in Use:**
```bash
# Find what's using port 5000
sudo lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Use different port
python app.py --port 8000
# Or modify app.py: app.run(port=8000)
```

### Performance Issues

**Slow Downloads:**
- Check internet connection speed
- Some platforms have rate limiting
- Try different quality settings
- Update yt-dlp: `pip install --upgrade yt-dlp`

**High Memory Usage:**
- Reduce concurrent downloads
- Clear old files regularly
- Monitor disk space

**Database Growing Too Large:**
```bash
# Clean up old records via admin panel
# Or manually:
sqlite3 downloads.db "DELETE FROM download_history WHERE created_at < datetime('now', '-30 days');"
```

### Platform-Specific Issues

**Instagram Downloads Failing:**
- Instagram frequently changes their API
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Some private accounts may not work

**YouTube Downloads Slow:**
- YouTube has rate limiting
- Try different quality options
- Consider using direct download for better performance

**TikTok Issues:**
- TikTok URLs change format frequently
- Ensure you're using the full URL, not shortened versions
- Update yt-dlp regularly

### Getting Help

**Enable Debug Mode:**
```python
# In app.py, change:
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Check Logs:**
```bash
# Run with output logging
python app.py > app.log 2>&1

# Monitor logs in real-time
tail -f app.log
```

**System Information for Support:**
```bash
# Gather system info for support requests
python --version
ffmpeg -version
pip list | grep -E "flask|yt-dlp|sqlalchemy"
uname -a  # Linux/macOS
systeminfo  # Windows
```

**Common Error Messages:**

- `ModuleNotFoundError: No module named 'flask'` → Virtual environment not activated or dependencies not installed
- `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'` → FFmpeg not installed or not in PATH
- `sqlite3.OperationalError: database is locked` → Database permission issues or multiple instances running
- `yt_dlp.utils.DownloadError` → URL not supported or platform blocking downloads
- `ConnectionError` → Internet connectivity issues

For additional support, check the GitHub issues or create a new issue with:
1. Your operating system
2. Python version
3. Error message (full traceback)
4. Steps to reproduce the problem



## 📝 API Documentation

### Public Endpoints

**POST /validate-url**
```json
{
  "url": "https://www.instagram.com/p/example/"
}
```

**POST /get-video-info**
```json
{
  "url": "https://www.instagram.com/p/example/"
}
```

**POST /download**
```json
{
  "url": "https://www.instagram.com/p/example/",
  "platform": "instagram",
  "format_id": "best",
  "type": "video"
}
```

### Response Format
```json
{
  "success": true,
  "filename": "instagram_20240101_120000_example.mp4",
  "file_size": 1048576,
  "download_url": "/download-file/filename.mp4"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with the terms of service of the platforms they download content from. Respect copyright laws and content creators' rights.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Use the contact form in the application
- Check the troubleshooting section above

---

**Version**: 1.0.0  
**Last Updated**: January 2025