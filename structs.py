import datetime
import pydantic


class VideoData(pydantic.BaseModel):
    channel_id: str
    id: str
    title: str
    description: str
    thumbnail: str
    created_at: datetime.datetime
