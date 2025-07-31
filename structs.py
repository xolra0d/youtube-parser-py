from datetime import datetime
from dataclasses import dataclass


@dataclass
class ChannelData:
    id: str
    title: str
    description: str
    thumbnail: str
    created_at: datetime
