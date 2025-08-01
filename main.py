import signal
import asyncio

from db import Inserter
from functions import create_logger
from parser import YoutubeAPIParser

logger = create_logger("main")

async def shutdown():
    all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"Cancelling {len(all_tasks)} tasks..")
    for task in all_tasks:
        task.cancel()


# EXAMPLE USAGE
async def main():
    logger.info("Starting parser...")
    loop = asyncio.get_running_loop()

    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown()))
    try:
        async with YoutubeAPIParser() as parser:
            await parser.run_forever()
    except asyncio.CancelledError:
        pass
    finally:
        try:
            async with Inserter() as inserter:
                await inserter.flush()
        except Exception as e:
            logger.error(f"Error during final flush: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
