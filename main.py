import asyncio

from structs import VideoData
from parser import YoutubeAPIParser

# EXAMPLE USAGE
async def print_random_channels():
    async with YoutubeAPIParser() as parser:
        random_channel_id = (await parser.get_new_channels_id("J33"))[0]
        random_video_info: VideoData = (await parser.get_videos(random_channel_id))[0]
        print(random_video_info)

asyncio.run(print_random_channels())
