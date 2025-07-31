import os
import httpx
import datetime
import typing as tp
from functools import wraps

from functions import create_logger
from structs import ChannelData

HTTPX_CONFIG = {
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
            config = HTTPX_CONFIG

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
    async def get_new_channels(self, q:str, count: int=50) -> list[ChannelData]:
        """Uses 100 quotas to find new channels"""
        if len(q) == 0:
            raise RuntimeError("Search query must not be empty")
        elif count <= 0:
            raise RuntimeError(f"Count must be positive. Given: {count}")

        end_point = f"/search?maxResults={count}&part=snippet&type=channel&q={q}&key={self.config['YOUTUBE_API_KEY']}"

        response = await self.client.get(end_point)
        if response.status_code != httpx.codes.OK:
            return []

        result = []
        for channel in response.json().get("items", []):
            result.append(ChannelData(
                id=channel["snippet"]["channelId"][2:], # first 2 letters indicate specific type: channel (UC). e.g. for playlist (UU)
                title=channel["snippet"]["title"],
                description=channel["snippet"]["description"],
                thumbnail=channel["snippet"]["thumbnails"]["default"]["url"],
                created_at=datetime.datetime.fromisoformat(channel["snippet"]["publishedAt"]),
            ))
        return result
