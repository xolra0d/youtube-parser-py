import signal
import asyncio

from db import Inserter
from functions import create_logger
from parser import YoutubeAPIParser


async def shutdown():
    print('You pressed Ctrl+C!')

    all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    print(f"Cancelling {len(all_tasks)} tasks..")
    for task in all_tasks:
        task.cancel()


# EXAMPLE USAGE
async def main():
    loop = asyncio.get_running_loop()

    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown()))
    try:
        async with YoutubeAPIParser() as parser:
            await parser.run_forever()
    except asyncio.CancelledError as e:
        pass
    finally:
        try:
            async with Inserter() as inserter:
                await inserter.flush()
        except Exception as e:
            create_logger("main").error(e)


asyncio.run(main())
