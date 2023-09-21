from pydantic.main import BaseModel
from pydantic import validator

class HighLightSchema(BaseModel):
    limit: int = 50000


class RequestSearchSchema(BaseModel):
    index: str
    query: dict
    limit: int | None
    offset: int | None
    max_matches: int | None
    sort: list[str] | None
    expressions: dict | None
    highlight: HighLightSchema | None
    source: list[str] | None
    options: dict | None = {"max_matches": 50_000}

    @validator("options")
    def compile_max_matches(cls, v, values):
        max_matches = values.get("max_matches")
        if max_matches:
            v["max_matches"] = max_matches
            return v

        limit = values.get("limit")
        offset = values.get("offset")
        if limit and offset:
            v["max_matches"] = limit + offset

        elif limit:
            v["max_matches"] = limit
        else:
            v["max_matches"] = 1000

        return v
