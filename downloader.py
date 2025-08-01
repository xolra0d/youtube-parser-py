import asyncio
import os
import yt_dlp
from pathlib import Path

from db import DownloaderDB


def download_video(url, output_path, quality="best"):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'format': f'{quality}[ext=mp4]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            print("Download completed successfully!")
    except Exception as e:
        print(f"Error downloading video: {str(e)}")


async def main():
    output_path = "./downloads"
    Path(output_path).mkdir(parents=True, exist_ok=True)
    try:
        while True:
            async with DownloaderDB() as db:
                for _ in range(5):
                    video_id = await db.get_random_video_id()
                    download_video(f"https://www.youtube.com/watch?v={video_id}", output_path)
                    await db.mark_downloaded(video_id)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nDownload interrupted by user. Cleaning up...")

import asyncio
asyncio.run(main())
