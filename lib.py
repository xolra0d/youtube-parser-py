import asyncio

from parser import YoutubeAPIParser

# EXAMPLE USAGE
async def print_random_channels():
    async with YoutubeAPIParser() as parser:
        channels = await parser.get_new_channels("H33")
        for channel in channels:
            print(channel)

asyncio.run(print_random_channels())
