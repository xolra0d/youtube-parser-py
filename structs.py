from datetime import datetime
from dataclasses import dataclass


@dataclass
class VideoData:
    channel_id: str
    channel_title: str
    id: str
    title: str
    description: str
    thumbnail: str
    created_at: datetime
