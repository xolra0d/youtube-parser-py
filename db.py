import asyncio
import typing as tp

import clickhouse_connect

from functions import create_logger
from structs import VideoData


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Inserter(metaclass=Singleton):
    def __init__(self, interval: int = 60, max_size: int = 150_000):
        self.table_name = "video_information"
        self.logger = create_logger(f"db.inserter.{self.table_name}")

        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue(maxsize=max_size)
        self.INTERVAL = interval
        self.client: tp.Optional[clickhouse_connect.driver.asyncclient.AsyncClient] = None

    async def __aenter__(self) -> 'Inserter':
        self.client = await clickhouse_connect.get_async_client()
        await self.create_table()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()
            self.client = None

    async def create_table(self):
        await self.client.command(f"""CREATE TABLE IF NOT EXISTS {self.table_name} (
    id String,
    title String,
    description String,
    thumbnail String,
    channel_id String,
    created_at String,
    is_downloaded Bool DEFAULT FALSE,
) ENGINE = ReplacingMergeTree()
ORDER BY (title, description);""")

    async def insert_async(self, *records: VideoData):
        await self.client.insert(
            self.table_name,
            [list(record.model_dump().values()) for record in records],
            column_names=list(records[0].model_dump().keys()),
            settings={
                "async_insert": 1,
                "wait_for_async_insert":0,
            },
        )

    async def flush(self):
        async with self.lock:
            batch = []
            size = self.queue.qsize()
            for _ in range(size):
                batch.append(self.queue.get_nowait())

        if not batch:
            return

        try:
            await self.insert_async(*batch)
            self.logger.info(f"Inserted {len(batch)} records")
        except Exception:
            self.logger.exception("Failed to flush data")

    async def insert_wait(self, record: VideoData):
        await self.queue.put(record)

    async def run(self):
        while True:
            await asyncio.sleep(self.INTERVAL)
            await self.flush()


class DownloaderDB(metaclass=Singleton):
    def __init__(self):
        self.table_name = "video_information"
        self.logger = create_logger(f"db.downloader.{self.table_name}")
        self.client: tp.Optional[clickhouse_connect.driver.asyncclient.AsyncClient] = None

    async def __aenter__(self) -> 'DownloaderDB':
        self.client = await clickhouse_connect.get_async_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()
            self.client = None

    async def get_random_video_id(self) -> str:
        while True:
            random_id = await self.client.query(
                f"""SELECT id
                FROM {self.table_name}
                WHERE is_downloaded = false
                ORDER BY cityHash64(concat(id, toString(now64())))
                LIMIT 1
                """
            )
            result_set =random_id.result_set
            if result_set:
                return result_set[0][0]
            await asyncio.sleep(5)

    async def mark_downloaded(self, video_id: str):
        await self.client.query(f"ALTER TABLE {self.table_name} UPDATE is_downloaded = false WHERE id = '{video_id}'")
