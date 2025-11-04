# YouTube Parser (Python)
___
**Fast async-based YouTube scraper**, which helps in <ins>official way</ins> to collect random video metadata and store it in a database for later use.
Example use: by ML engineers who need video samples for training AI models.
Additionally, they can be filtered by title, description, duration, etc.
BEFORE START GET YOUR API_KEY: https://developers.google.com/youtube/v3/getting-started
___
## Features
- Find random channels or videos using YouTube Data API V3
- Store metadata in **SQLite** DB
- Additionally, opt for background downloading of videos
- Fully async using `asyncio` + `httpx`
- Optional: video downloading to directory (`.mp4`) using `yt-dlp`
- Plug and play like project
___
## Performance (at 50 Mb/s)
- Uses current whole free user quota (10000 points/day) in 22 min.
- In average, 27 videos/1 api point => ~270000 videos scanned for free quota.
- In average, 12000 videos / minute
---
## Modules
- `structs.py` - structs required for parser logic
- `parser.py` - main scraper logic
- `db.py` - interface for writing to SQLite
- `downloader.py` - module for downloading videos
- `main.py` - running file
___
## Installation & Usage
1. [install ffmpeg](https://ffmpeg.org/download.html)
2. `pip3 install -r requirements.txt` - install requirements
3. `YOUTUBE_API_KEY=YOUR_KEY python3 main.py` - main scraping logic
4. `python3 downloader.py` - downloading logic
___
## Tech Stack
- [`asyncio`](https://docs.python.org/3/library/asyncio.html) – concurrency
- [`httpx`](https://www.python-httpx.org/) – async HTTP requests
- [`AIOSQLite`](https://pypi.org/project/aiosqlite/) – fast and small database used for structured video data
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) + `ffmpeg` – video downloading
___
## License
- MIT
