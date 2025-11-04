import asyncio
import logging
import typing as tp
import aiosqlite

from structs import VideoData


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Inserter(metaclass=Singleton):
    logger = logging.getLogger(f"db.inserter")

    def __init__(self, interval: int = 60, max_size: int = 150_000, db_path: str = "youtube_videos.db"):
        self.table_name = "video_information"
        self.db_path = db_path

        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue(maxsize=max_size)
        self.INTERVAL = interval
        self.db: tp.Optional[aiosqlite.Connection] = None

    async def __aenter__(self) -> 'Inserter':
        self.db = await aiosqlite.connect(self.db_path)
        await self.create_table()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()
            self.db = None

    async def create_table(self):
        await self.db.execute(f"""CREATE TABLE IF NOT EXISTS {self.table_name} (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    thumbnail TEXT,
    channel_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_downloaded INTEGER DEFAULT 0
)""")
        await self.db.execute(f"CREATE INDEX IF NOT EXISTS idx_is_downloaded ON {self.table_name}(is_downloaded)")
        await self.db.commit()

    async def insert_async(self, *records: VideoData):
        data = [
            (
                record.id,
                record.title,
                record.description,
                record.thumbnail,
                record.channel_id,
                record.created_at.isoformat(),
            )
            for record in records
        ]
        
        await self.db.executemany(
            f"""INSERT OR REPLACE INTO {self.table_name} 
            (id, title, description, thumbnail, channel_id, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            data
        )
        await self.db.commit()

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
        except Exception as _:
            self.logger.exception("Failed to flush data")
        finally:
            batch.clear()

    async def insert_wait(self, record: VideoData):
        await self.queue.put(record)

    async def run(self):
        while True:
            await asyncio.sleep(self.INTERVAL)
            await self.flush()


class DownloaderDB(metaclass=Singleton):
    def __init__(self, db_path: str = "youtube_videos.db"):
        self.table_name = "video_information"
        self.logger = logging.getLogger(f"db.downloader.{self.table_name}")
        self.db_path = db_path
        self.db: tp.Optional[aiosqlite.Connection] = None

    async def __aenter__(self) -> 'DownloaderDB':
        self.db = await aiosqlite.connect(self.db_path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()
            self.db = None

    async def get_random_video_id(self) -> str:
        while True:
            async with self.db.execute(
                f"""SELECT id
                FROM {self.table_name}
                WHERE is_downloaded = 0
                ORDER BY RANDOM()
                LIMIT 1
                """
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
            await asyncio.sleep(5)

    async def mark_downloaded(self, video_id: str):
        await self.db.execute(
            f"UPDATE {self.table_name} SET is_downloaded = 1 WHERE id = ?",
            (video_id,)
        )
        await self.db.commit()
