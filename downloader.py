import os
import yt_dlp
import asyncio
import logging
from pathlib import Path

from db import DownloaderDB

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

shutdown_requested = False


def download_video_sync(url: str, output_path: Path):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'socket_timeout': 30,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def download_video(url: str, output_path: Path):
    global shutdown_requested
    try:
        await asyncio.to_thread(download_video_sync, url, output_path)
        logger.info(f"Download completed successfully: {url}")
        return True
    except KeyboardInterrupt:
        logger.info("Shutdown requested, will exit after current download completes")
        shutdown_requested = True
        return True
    except Exception as e:
        logger.error(f"Error downloading video {url}: {type(e).__name__}: {e}")
        return False


async def main():
    output_path = Path("./downloads")
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        async with DownloaderDB() as db:
            while True:
                video_id = await db.get_random_video_id()
                if video_id is None:
                    logger.warning("No video IDs available in database, waiting...")
                    await asyncio.sleep(10)
                    continue

                logger.info(f"Starting download for video: {video_id}")

                url = f"https://www.youtube.com/watch?v={video_id}"
                success = await download_video(url, output_path)

                if success:
                    await db.mark_downloaded(video_id)
                    logger.info(f"Marked video as downloaded: {video_id}")
                
                if shutdown_requested:
                    logger.info("Shutdown complete. Exiting...")
                    break
                
                if success:
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"Failed to download video, will retry later: {video_id}")
                    await asyncio.sleep(5)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Download interrupted by user. Cleaning up...")

if __name__ == "__main__":
    asyncio.run(main())
