import os
import httpx
import random
import string
import asyncio
import datetime
import typing as tp
from functools import wraps

from db import Inserter
from structs import VideoData
from functions import create_logger

CONFIG = {
    "YOUTUBE_API_KEY": os.environ.get("YOUTUBE_API_KEY"),
    "timeout": httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=5.0,
    ),
    "limits": httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0,
    ),
    "headers": httpx.Headers({
        "User-Agent": "Parser/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }),
    "follow_redirects": True,
    "verify": True,
    "semaphore": asyncio.Semaphore(6),
}


def validate_client(func: tp.Callable) -> tp.Callable:
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.client is None:
            raise RuntimeError("Parser must be used as a async context manager")
        return await func(self, *args, **kwargs)
    return wrapper


class YoutubeAPIParser:
    def __init__(self, base_url: str = "https://www.googleapis.com/youtube/v3", config = None) -> None:
        if config is None:
            config = CONFIG

        self.client: tp.Optional[httpx.AsyncClient] = None
        self.config = config
        self.base_url = base_url
        self.logger = create_logger("YoutubeAPIParser")

    async def __aenter__(self) -> 'YoutubeAPIParser':
        self.client = httpx.AsyncClient(
            timeout=self.config["timeout"],
            limits=self.config["limits"],
            headers=self.config["headers"],
            follow_redirects=self.config["follow_redirects"],
            verify=self.config["verify"],
            base_url=self.base_url,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    @validate_client
    async def get_new_channels_id(self, q:str, count: int=50) -> list[str]:
        """Uses 100 quotas to find new channels id"""
        if len(q) == 0:
            raise RuntimeError("Search query must not be empty")
        elif count <= 0:
            raise RuntimeError(f"Count must be positive. Given: {count}")

        end_point = f"/search?maxResults={count}&part=snippet&type=channel&q={q}&key={self.config['YOUTUBE_API_KEY']}"

        response = await self.client.get(end_point)
        if response.status_code != httpx.codes.OK:
            return []

        results = []
        for channel in response.json().get("items", []):
            results.append(channel["snippet"]["channelId"][2:]) # first 2 letters indicate specific type: channel (UC). e.g. for playlist (UU)

        return results

    @validate_client
    async def get_videos(self, channel_id: str, inserter) -> list[VideoData]:
        """Uses 1 quota to find new channels"""
        async with self.config["semaphore"]:
            playlist_id = "UU" + channel_id
            end_point = f"/playlistItems?part=snippet%2CcontentDetails&maxResults=50&playlistId={playlist_id}&key={self.config['YOUTUBE_API_KEY']}" # &pageToken={next_page_token}

            response = await self.client.get(end_point)
            if response.status_code != httpx.codes.OK:
                return []

            results = []

            while True:
                data = response.json()
                for video in data["items"]:
                    snippet = video["snippet"]

                    thumbnail_url = None
                    thumbnails = snippet.get("thumbnails", {})
                    if "maxres" in thumbnails:
                        thumbnail_url = thumbnails["maxres"]["url"]
                    elif "high" in thumbnails:
                        thumbnail_url = thumbnails["high"]["url"]
                    elif "medium" in thumbnails:
                        thumbnail_url = thumbnails["medium"]["url"]

                    await inserter.insert_wait(VideoData(
                        channel_id=snippet["channelId"],
                        id=video["contentDetails"]["videoId"],
                        title=snippet["title"],
                        description=snippet["description"],
                        thumbnail=thumbnail_url,
                        created_at=datetime.datetime.fromisoformat(snippet["publishedAt"]),
                    ))

                next_page_token = data.get("nextPageToken")

                if next_page_token is None: break
                response = await self.client.get(end_point + f"&pageToken={next_page_token}")
                if response.status_code != httpx.codes.OK:
                    break
            return results

    async def run_once(self):
        chars = string.digits + string.ascii_letters
        random_q = random.choice(chars) + random.choice(chars) + random.choice(chars)

        channels: list[int] = await self.get_new_channels_id(random_q)
        async with Inserter() as inserter:
            tasks = [asyncio.create_task(self.get_videos(channel_id, inserter)) for channel_id in channels]
            await asyncio.gather(*tasks)
            await inserter.flush()


    async def run_forever(self):
        while True:
            await self.run_once()
