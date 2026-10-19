<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader">
    <h3 align="center">Social Media Downloader</h3>
  </a>

  <p align="center">
    A self-hosted Flask application that pulls media from Instagram, TikTok, Facebook,
    Twitter/X, YouTube, and Reddit with yt-dlp, and exposes it through a small admin panel.
    <br />
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader"><strong>Explore the source »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/blob/main/routes.py">Public routes</a>
    &middot;
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/blob/main/admin.py">Admin routes</a>
    &middot;
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#how-downloads-work">How Downloads Work</a></li>
        <li><a href="#file-retention">File Retention</a></li>
        <li><a href="#known-issue-read-this-first">Known Issue: Read This First</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#configuration">Configuration</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#web-interface">Web Interface</a></li>
        <li><a href="#api">API</a></li>
        <li><a href="#running-in-production">Running in Production</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li>
      <a href="#contributing">Contributing</a>
      <ul>
        <li><a href="#top-contributors">Top contributors:</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

A Flask application that takes a social media URL, downloads the media server-side with
`yt-dlp`, optionally converts it to MP3 with FFmpeg, and serves it back for one download before
deleting it. Around that core there is a session-authenticated admin panel for download
history, statistics, blog posts, legal pages, and contact messages.

It is deliberately small — four Python modules, Jinja templates, and one vanilla JavaScript
file. There is no build step, no bundler, and no frontend framework; `static/css/style.css`
and `static/js/main.js` are served as-is. The only external process the app shells out to is
`ffmpeg`.

The URL allowlist is explicit. `validate_url()` in `utils.py` parses the hostname and rejects
anything outside `instagram.com`, `tiktok.com` / `vm.tiktok.com`, `facebook.com` / `fb.watch`,
`twitter.com` / `x.com`, `youtube.com` / `youtu.be`, and `reddit.com`; `detect_platform()`
maps the same hostnames to one of six platform keys.

**Scope and responsibility.** This is an infrastructure project: the interesting part is the
orchestration, the retention policy, and the admin surface. You are responsible for complying
with the terms of service of whichever platform you point it at, and with the rights of the
people whose content you download.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### How Downloads Work

`POST /download` takes `{url, platform, format_id, type}` and branches on `format_id`:

| Request | Path taken |
| --- | --- |
| `format_id` omitted | `download_media()` — single-pass `best[height<=720]/best`, filename derived from the cleaned title |
| `format_id == "best"` and `type == "video"` | `download_media_with_format()` — `bestvideo[ext=mp4]+bestaudio[ext=m4a]` merged with FFmpeg into `mp4` |
| `format_id` set and `type == "video"` | `get_direct_download_url()` — returns a direct link instead of downloading |
| `type == "audio"` | `download_media_with_format()` downloads the best video, runs `ffmpeg -i in.mp4 -vn -ab 192k -ar 44100 out.mp3`, then deletes the intermediate video |

Server-side downloads are written into `downloads/` and recorded in `download_history` with
the URL, platform, filename, path, byte size, and media type. Direct downloads are not
recorded — nothing touches the disk.

`get_video_info()` (`POST /get-video-info`) does an `extract_info(..., download=False)` pass to
return title, duration, an estimated size, and a thumbnail. Instagram thumbnails are fetched
server-side into `static/thumbnails/` and served locally, because Instagram's CDN URLs do not
render reliably in a browser `<img>`.

The six quality options defined in `get_available_formats()` — `best`, `worst[height>=480]`,
`worst` for video and `bestaudio`, `bestaudio[abr>=96]`, `worstaudio` for audio — are available
to the API. Note that the bundled front end does not currently send `format_id`, so a download
started from the UI takes the first row of that table.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### File Retention

Two independent mechanisms, both deliberate:

1. **Forty-second timer.** `GET /download-file/<filename>` schedules a `threading.Timer(40.0, …)`
   that deletes the file *and* its `download_history` row once the response has been served.
2. **Hourly sweeper.** A daemon thread started at import time in `routes.py` wakes every 3600
   seconds, removes anything in `downloads/` older than 24 hours, and deletes the corresponding
   history rows.

`GET /history` shows the most recent 50 records. `POST /delete-history/<id>` removes a row and
its file immediately. `POST /admin/api/cleanup` accepts `{"days": 7}` and returns how many
files and records were removed and how much space was freed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Known Issue: Read This First

`routes.py` line 24 does:

```python
from utils_direct import get_direct_download_url
```

There is no `utils_direct.py` in this repository, and no rule in `.gitignore` that would explain
its absence. Because `app.py` runs `from routes import *` at module scope, the import fails
before the app object is served and `python app.py` exits with `ModuleNotFoundError: No module
named 'utils_direct'`.

This is the first thing to fix before anything else in this README will work. `get_direct_download_url`
is used by the `format_id`-specified video branch of `/download`, and by the `/youtube-proxy`
response shape. If you are pulling this down to run it, either restore the module or provide the
function yourself:

```python
# utils_direct.py
def get_direct_download_url(url, platform, format_id, download_type):
    """Return {'success': False, 'error': 'not implemented'} to keep the app importable."""
    return {'success': False, 'error': 'Direct downloads are not available'}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Flask][Flask]][Flask-url]
* [![Python][Python]][Python-url]
* [![Jinja][Jinja]][Jinja-url]
* ![![SQLAlchemy][SQLAlchemy]][SQLAlchemy-url]
* [![SQLite][SQLite]][SQLite-url]
* [![yt-dlp][yt-dlp]][yt-dlp-url]
* [![FFmpeg][FFmpeg]][FFmpeg-url]
* [![Gunicorn][Gunicorn]][Gunicorn-url]
* ![![Mistune][Mistune]][Mistune-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* Python 3.11+ (`pyproject.toml` sets `requires-python = ">=3.11"`)
  ```sh
  python3 --version
  ```
* FFmpeg — required for both video merging and MP3 conversion. The app shells out to `ffmpeg`
  directly; there is no bundled binary.
  ```sh
  # Ubuntu / Debian
  sudo apt update && sudo apt install ffmpeg

  # macOS
  brew install ffmpeg

  # Windows
  winget install Gyan.FFmpeg
  ```
  Verify with `ffmpeg -version`.
* A writable `downloads/` directory and, for Instagram thumbnails, a writable
  `static/thumbnails/` directory. Both are created on demand.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/Elouahabi-Naoufal/Social-Media-Downloader.git
   cd Social-Media-Downloader
   ```

2. Create a virtual environment
   ```sh
   python3 -m venv env
   source env/bin/activate        # Windows: env\Scripts\activate
   ```

3. Install dependencies. `requirements.txt` and `pyproject.toml` both exist and are kept in
   sync; `uv.lock` is committed, so `uv sync` also works if you prefer it.
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt

   # or, with uv
   uv sync
   ```
   Note that `requirements.txt` and `pyproject.toml` are not identical: `pyproject.toml` also
   declares the `social-media-downloader` package, which no module in this repository imports.
   `requirements.txt` is the list that actually matches the code.

4. Create the runtime directories
   ```sh
   mkdir -p downloads static/thumbnails
   ```

5. Fix the missing module described in [Known Issue](#known-issue-read-this-first), then start
   the app
   ```sh
   python app.py
   ```
   `app.py` calls `db.create_all()` at import time, so the SQLite file and its five tables are
   created on the first successful start. The server binds `0.0.0.0:5000` with `debug=False`.

### Configuration

Four environment variables are read by the code. There is no `python-dotenv` dependency and
nothing calls `load_dotenv()`, so a `.env` file on disk will **not** be picked up — either
export them in the shell or source the file first.

| Variable | Read in | Default | Purpose |
| --- | --- | --- | --- |
| `SESSION_SECRET` | `app.py:18` | `dev-secret-key-change-in-production` | Flask session signing key |
| `DATABASE_URL` | `app.py:22` | `sqlite:///downloads.db` | SQLAlchemy connection string |
| `ADMIN_USERNAME` | `admin.py:17` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `admin.py:18` | `admin123` | Admin login password |

```sh
export SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_USERNAME="your-username"
export ADMIN_PASSWORD="a-long-unique-password"
export DATABASE_URL="sqlite:///instance/downloads.db"

python app.py
```

Or with a `.env` file and no extra dependency:

```sh
set -a; . ./.env; set +a
python app.py
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Web Interface

| Path | What it is |
| --- | --- |
| `/` | Download form — paste a URL, pick a platform or auto-detect |
| `/history` | Last 50 downloads, with per-item delete |
| `/blog`, `/blog/<slug>` | Blog, published posts only |
| `/legal`, `/legal/<slug>` | Legal page index |
| `/privacy`, `/terms` | Shortcuts to the `privacy-policy` and `terms-of-service` pages |
| `/contact` | Contact form, stored as `contact_messages` rows |
| `/admin/login` | Admin sign-in |
| `/admin` | Dashboard — totals, per-platform counts, 7-day trend, recent activity |
| `/admin/downloads` | Paginated history with platform filter and free-text search |
| `/admin/analytics` | Hourly / day-of-week / monthly / per-platform breakdowns |
| `/admin/blog`, `/admin/legal` | Markdown authoring with image upload and publish toggle |
| `/admin/messages` | Contact submissions, with mark-read toggle |
| `/admin/settings` | Storage usage and database record bounds |

Admin routes are gated by an `@admin_required` decorator that checks `session['admin_logged_in']`
and redirects to `/admin/login`.

### API

```sh
# Validate a URL and detect the platform
curl -X POST http://localhost:5000/validate-url \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://www.instagram.com/p/example/"}'
# {"valid": true, "platform": "instagram"}

# Metadata without downloading
curl -X POST http://localhost:5000/get-video-info \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://www.instagram.com/p/example/"}'
# {"success": true, "title": "...", "duration": "0:27", "thumbnail": "/static/thumbnails/thumb_xxxxxxxx.jpg",
#  "platform": "instagram", "file_size": "4.7 MB"}

# Download (server-side, best quality up to 720p)
curl -X POST http://localhost:5000/download \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://www.instagram.com/p/example/", "platform": "instagram"}'
# {"success": true, "filename": "instagram_20250114_120530_Example_Post_ab12cd.mp4",
#  "file_size": 4921088, "media_type": "video",
#  "download_url": "/download-file/instagram_..._ab12cd.mp4", "message": "Video downloaded successfully!"}

# Download and merge to the highest quality
curl -X POST http://localhost:5000/download \
  -H 'Content-Type: application/json' \
  -d '{"url": "...", "platform": "youtube", "format_id": "best", "type": "video"}'

# Extract audio as MP3 (192 kbps, 44.1 kHz)
curl -X POST http://localhost:5000/download \
  -H 'Content-Type: application/json' \
  -d '{"url": "...", "platform": "youtube", "type": "audio"}'

# Delete a history row and its file
curl -X POST http://localhost:5000/delete-history/42
```

Admin JSON endpoints, all requiring a logged-in session:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/admin/api/stats` | Totals, storage size, 24-hour hourly activity |
| `DELETE` | `/admin/api/delete-download/<id>` | Delete one download and its file |
| `POST` | `/admin/api/cleanup` | `{"days": 7}` — purge files and records older than N days |
| `POST` | `/admin/api/upload-image` | Store an image in the DB, return `/image/<uuid>.<ext>` |
| `POST` | `/admin/api/toggle-blog/<id>` | Publish / unpublish a post |
| `DELETE` | `/admin/api/delete-blog/<id>` | Delete a post |
| `POST` | `/admin/api/toggle-legal/<id>` | Publish / unpublish a legal page |
| `DELETE` | `/admin/api/delete-legal/<id>` | Delete a legal page |
| `POST` | `/admin/api/mark-read/<id>` | Toggle read state on a message |
| `DELETE` | `/admin/api/delete-message/<id>` | Delete a message |

Data model: `download_history`, `blogs`, `images`, `legal_pages`, `contact_messages`. Blog and
legal-page bodies are stored twice — `raw_content` keeps the original Markdown, `content` keeps
the mistune-rendered HTML — so posts can be re-rendered or re-exported later. Thumbnails and
uploaded images are `LargeBinary` columns served back through `/blog-thumbnail/<id>`,
`/legal-thumbnail/<id>`, and `/image/<filename>` with a one-year `Cache-Control`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Running in Production

`gunicorn` is already a dependency:

```sh
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 2 app:app
```

`app.py` wraps the WSGI app in `werkzeug.middleware.proxy_fix.ProxyFix` for `X-Proto` and
`X-Host`, so running behind a TLS-terminating reverse proxy works as long as the proxy sets
those headers. Set the four environment variables from the table above before starting —
in particular `SESSION_SECRET`, since the default is a fixed string that anyone reading the
repository knows.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] yt-dlp download pipeline with video, merged-best, and MP3 paths
- [x] URL allowlist and platform detection for six platforms
- [x] Download history with per-item delete and an hourly retention sweeper
- [x] Admin panel: dashboard, download management, analytics, blog, legal pages, messages,
      settings
- [x] Markdown authoring with DB-backed images and thumbnails
- [ ] **Restore or replace `utils_direct.py`.** Without it the app does not import. This blocks
      everything else.
- [ ] Hash the admin password. `hash_password()` and `verify_password()` are already written
      with SHA-256 but are never called — `admin_login` compares `request.form['password']`
      directly against the plaintext `ADMIN_PASSWORD` environment variable.
- [ ] CSRF protection on the admin POST endpoints and the contact form. There is currently no
      token on any of them.
- [ ] Rate limiting on `/download` and `/youtube-proxy`, which both make outbound requests to
      arbitrary platforms on behalf of an anonymous caller. `/youtube-proxy` in particular
      fetches a caller-supplied `url` server-side.
- [ ] Wire the quality selectors into the front end. `get_available_formats()` returns six
      options, but `main.js` never sends `format_id`, so the direct-download and medium/low
      branches are unreachable from the UI.
- [ ] Decide on the `DATABASE_URL` story. `psycopg2-binary` is a dependency and the URL is
      honoured, but the analytics queries use SQLite-specific `func.extract()` and
      `func.strftime()`, so `/admin/analytics` will not work against PostgreSQL as written.
- [ ] Add tests. There is no test directory or test runner configuration in the repository.
- [ ] Add a `.env` loader, or document `set -a; . ./.env; set +a` everywhere, since a plain
      `.env` file is silently ignored today.
- [ ] Reconcile `pyproject.toml` with `requirements.txt` — the former declares a
      `social-media-downloader` dependency that nothing in the code imports.

See the [open issues](https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Before opening a pull request, set `SESSION_SECRET`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` and
confirm `python app.py` starts cleanly. If you touch the download path, exercise at least one
video and one audio conversion with FFmpeg on `PATH`.

### Top contributors:

<a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Elouahabi-Naoufal/Social-Media-Downloader" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

No license file is currently bundled with this repository. Until one is added, the default GitHub
terms apply and the repository should be treated as unlicensed — do not redistribute it without
asking.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Naoufal Elouahabi - [LinkedIn](https://www.linkedin.com/in/elouahabi-naoufal/) - elouahabi-naoufal1@gmail.com

Project Link: [https://github.com/Elouahabi-Naoufal/Social-Media-Downloader](https://github.com/Elouahabi-Naoufal/Social-Media-Downloader)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [yt-dlp](https://github.com/yt-dlp/yt-dlp) — all extraction and downloading.
* [FFmpeg](https://ffmpeg.org) — stream merging and MP3 transcoding.
* [Flask](https://flask.palletsprojects.com) and [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com)
* [mistune](https://mistune.readthedocs.io) — Markdown rendering for blog and legal pages.
* [Werkzeug](https://werkzeug.palletsprojects.com) — `ProxyFix` and `send_file`.
* [Img Shields](https://shields.io)
* [Choose an Open Source License](https://choosealicense.com)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[contributors-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[forks-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/network/members
[stars-shield]: https://img.shields.io/github/stars/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[stars-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/stargazers
[issues-shield]: https://img.shields.io/github/issues/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[issues-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues
[license-shield]: https://img.shields.io/github/license/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[license-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/elouahabi-naoufal/
[Flask]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Jinja]: https://img.shields.io/badge/Jinja-B41717?style=for-the-badge&logo=jinja&logoColor=white
[Jinja-url]: https://jinja.palletsprojects.com/
[SQLAlchemy]: https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white
[SQLAlchemy-url]: https://www.sqlalchemy.org/
[SQLite]: https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white
[SQLite-url]: https://www.sqlite.org/
[yt-dlp]: https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white
[yt-dlp-url]: https://github.com/yt-dlp/yt-dlp
[FFmpeg]: https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white
[FFmpeg-url]: https://ffmpeg.org/
[Gunicorn]: https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white
[Gunicorn-url]: https://gunicorn.org/
[Mistune]: https://img.shields.io/badge/mistune-3776AB?style=for-the-badge
[Mistune-url]: https://mistune.readthedocs.io/