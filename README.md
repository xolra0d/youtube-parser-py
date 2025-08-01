# YouTube Parser (Python)
___
**Fast async-based YouTube scraper**, which helps you in <ins>official way</ins> to collect random video metadata and store it in a database for later use.
Example use: by ML engineers who need video samples for training AI models.
Additionally, they can be filtered by title, description, duration, etc.
___
## Features
- Find random channels or videos using YouTube Data API V3
- Store metadata in **ClickHouse** DB
- Additionally, opt for background downloading of videos
- Fully async using `asyncio` + `httpx`
- Optional: video downloading to directory (`.mp4`) using `yt-dlp`
- Plug and play like project
___
## Modules
- `functions.py` - additional functions
- `structs.py` - structs required for parser logic
- `parser.py` - main scraper logic
- `db.py` - interface for writing to ClickHouse
- `downloader.py` - module for downloading videos
- `main.py` - running file
___
## Installation & Usage
1. [Install ClickHouse](https://clickhouse.com/docs/install)
2. [install ffmpeg](https://ffmpeg.org/download.html)
2. `pip3 install -r requirements.txt` - install requirements
3. `python3 main.py` - main scraping logic
4. `python3 downloader.py` - downloading logic
___
## Tech Stack
- [`asyncio`](https://docs.python.org/3/library/asyncio.html) – concurrency
- [`httpx`](https://www.python-httpx.org/) – async HTTP requests
- [`ClickHouse`](https://clickhouse.com/) – fast OLAP database for structured video data
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) + `ffmpeg` – video downloading
___
## License
- MIT
