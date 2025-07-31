import asyncio

from structs import VideoData
from parser import YoutubeAPIParser

# EXAMPLE USAGE
async def main():
    async with YoutubeAPIParser() as parser:
        await parser.run_once()
