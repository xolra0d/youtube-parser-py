import datetime
import typing as tp
import pydantic


class VideoData(pydantic.BaseModel):
    channel_id: str
    id: str
    title: str
    description: str
    thumbnail: tp.Optional[str]
    created_at: datetime.datetime
