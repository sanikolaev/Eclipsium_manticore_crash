from datetime import datetime

from pydantic import BaseModel
from pydantic.class_validators import validator


class PostSchema(BaseModel):
    id: int
    posted: datetime | float
    uploaded_at: float | None
    title: str | None
    content: str | None
    source_id: int
    is_blogger: bool
    source_type: str

    @validator("content", "title")
    def replace_null_empty_str(cls, v):
        if isinstance(v, str):
            return v
        return ""

    @validator("posted", "uploaded_at", always=True)
    def convert_to_unix_timestamp(cls, v):
        if not v:
            # для uploaded_at выставляем дату сразу
            # Схема переведет ее в timestamp
            v = datetime.now()

        if isinstance(v, datetime):
            try:
                return int(datetime.timestamp(v))
            except OSError:
                raise ValueError("Дата слишком большая для представления в timestamp")

        return v
