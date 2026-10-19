<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <h3 align="center">Social Media Downloader</h3>

  <p align="center">
    A self-hosted Flask application that downloads media from Instagram, TikTok, Facebook,
    Twitter/X, YouTube and Reddit with yt-dlp, with history and an admin panel.
    <br />
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader"><strong>Explore the source »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## About The Project

Social Media Downloader takes a supported URL, downloads the media server-side with `yt-dlp`,
optionally extracts audio with FFmpeg, and serves the result before deleting it shortly afterwards.
A session-authenticated admin panel adds history, statistics, blog posts, legal pages and contact
messages.

The URL allowlist in `utils.py` accepts:

* `instagram.com`
* `tiktok.com` and `vm.tiktok.com`
* `facebook.com` and `fb.watch`
* `twitter.com` and `x.com`
* `youtube.com` and `youtu.be`
* `reddit.com`

Downloaded files are written to `downloads/` and recorded in `download_history`. The application
also includes:

* Video download, merged-best video/audio, and MP3 audio extraction
* Video metadata and thumbnail lookup before downloading
* A public history page and per-item deletion
* An hourly sweeper that removes files older than 24 hours
* An admin dashboard, analytics, blog/legal content management and contact inbox

**Known issue:** `routes.py` imports `get_direct_download_url` from `utils_direct`, but
`utils_direct.py` is not committed. Because `app.py` imports `routes` at module scope, the app
exits with `ModuleNotFoundError` until that module is restored or replaced.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Python][Python]][Python-url]
* [![Flask][Flask]][Flask-url]
* [![SQLite][SQLite]][SQLite-url]
* [![yt-dlp][yt-dlp]][yt-dlp-url]
* [![FFmpeg][FFmpeg]][FFmpeg-url]
* [![Gunicorn][Gunicorn]][Gunicorn-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

* Python 3.11+ (`pyproject.toml` declares `requires-python = ">=3.11"`)
* FFmpeg for merging and MP3 extraction
  ```sh
  # Ubuntu / Debian
  sudo apt update && sudo apt install ffmpeg
  ```

### Installation

1. Clone the repository
   ```sh
   git clone https://github.com/Elouahabi-Naoufal/Social-Media-Downloader.git
   cd Social-Media-Downloader
   ```

2. Create a virtual environment and install dependencies
   ```sh
   python3 -m venv env
   source env/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Create the runtime directories
   ```sh
   mkdir -p downloads static/thumbnails
   ```

4. Restore the missing `utils_direct` module. A minimal placeholder that keeps the app
   importable is:
   ```python
   # utils_direct.py
   def get_direct_download_url(url, platform, format_id, download_type):
       return {"success": False, "error": "Direct downloads are not available"}
   ```

5. Configure the environment. The code reads these variables directly; it does not load a
   `.env` file, so export them in your shell.
   ```sh
   export SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
   export DATABASE_URL="sqlite:///instance/downloads.db"
   export ADMIN_USERNAME="admin"
   export ADMIN_PASSWORD="replace-with-a-strong-password"
   ```

6. Start the app
   ```sh
   python app.py
   ```

7. Open <http://localhost:5000>

Production:
```sh
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --keep-alive 2 app:app
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

| Path | Purpose |
| --- | --- |
| `/` | Paste a URL and start a download |
| `/history` | Last 50 downloads with deletion |
| `/blog` | Published blog posts |
| `/legal` | Legal pages |
| `/contact` | Contact form stored in the database |
| `/admin/login` | Admin sign-in |
| `/admin` | Dashboard and platform statistics |
| `/admin/downloads` | Download history with filters |
| `/admin/analytics` | Time and platform breakdowns |
| `/admin/blog`, `/admin/legal` | Markdown content management |
| `/admin/messages` | Contact inbox |

Public endpoints include `/validate-url`, `/get-video-info`, `/download`,
`/download-file/<filename>` and `/delete-history/<id>`. Admin JSON endpoints live under
`/admin/api/` and require a logged-in admin session.

Files are deleted 40 seconds after a download response is served, and the hourly sweeper removes
any remaining files older than 24 hours.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [x] yt-dlp download pipeline for video, merged-best and MP3
- [x] URL allowlist and platform detection for six platforms
- [x] History, per-item deletion and retention sweeper
- [x] Admin dashboard, analytics, blog, legal pages and contact inbox
- [ ] Restore the missing `utils_direct.py`
- [ ] Send `format_id` from the bundled front end so quality selection is used
- [ ] Add automated tests for URL validation and download routing
- [ ] Add rate limiting to the public download endpoints

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire,
and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Top contributors:

<a href="https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Elouahabi-Naoufal/Social-Media-Downloader" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

This project is not licensed — all rights reserved.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Naoufal Elouahabi - [LinkedIn](https://www.linkedin.com/in/elouahabi-naoufal/) - elouahabi-naoufal1@gmail.com

Project Link: [https://github.com/Elouahabi-Naoufal/Social-Media-Downloader](https://github.com/Elouahabi-Naoufal/Social-Media-Downloader)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [Flask](https://flask.palletsprojects.com/)
* [FFmpeg](https://ffmpeg.org/)
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
* [Img Shields](https://shields.io)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[contributors-shield]: https://img.shields.io/github/contributors/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[contributors-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[forks-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/network/members
[stars-shield]: https://img.shields.io/github/stars/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[stars-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/stargazers
[issues-shield]: https://img.shields.io/github/issues/Elouahabi-Naoufal/Social-Media-Downloader.svg?style=for-the-badge
[issues-url]: https://github.com/Elouahabi-Naoufal/Social-Media-Downloader/issues
[license-shield]: https://img.shields.io/badge/license-none-lightgrey?style=for-the-badge
[license-url]: #license
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/elouahabi-naoufal/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flask]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[SQLite]: https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white
[SQLite-url]: https://www.sqlite.org/
[yt-dlp]: https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white
[yt-dlp-url]: https://github.com/yt-dlp/yt-dlp
[FFmpeg]: https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white
[FFmpeg-url]: https://ffmpeg.org/
[Gunicorn]: https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white
[Gunicorn-url]: https://gunicorn.org/
