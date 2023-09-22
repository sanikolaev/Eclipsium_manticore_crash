import asyncio
import random
from datetime import UTC, datetime, timedelta

import httpx
from loguru import logger
from lorem_text import lorem

from insert_document_schema import InsertDocumentSchema, \
    BulkIReplaceDocumentSchema
from post_schema import PostSchema
from search_schema import RequestSearchSchema

BASE_URL = "http://manticore:9308"
INDEX_STMT = (
    "CREATE TABLE posts_idx ("
    "id BIGINT, "
    "posted TIMESTAMP, "
    "uploaded_at TIMESTAMP, "
    "title TEXT, "
    "content TEXT, "
    "source_type STRING,  "
    "source_id INTEGER, "
    "is_blogger BOOL) "
    "index_exact_words = '1' "
    "morphology = 'lemmatize_ru_all, lemmatize_en_all' "
    "charset_table = '0..9, english, russian, _'")


async def insert_to_manticore():
    while True:
        posts = [
            PostSchema(
                id=random.randint(1, 2 ** 31),
                posted=int(datetime.now(tz=UTC).timestamp()),
                uploaded_at=int(datetime.now(tz=UTC).timestamp()),
                title=lorem.sentence(),
                content=lorem.paragraphs(5),
                source_id=random.randint(1, 5),
                is_blogger=bool(random.randint(0, 1)),
                source_type=random.choice(["SMI", "BLOGGER"])
            ) for _ in range(2000)
        ]
        payload = []

        for post in posts:
            try:
                insert_stmt = InsertDocumentSchema(
                    index="posts_idx",
                    id=post.id,
                    doc=post.dict(exclude={"id"}),
                )
            except ValueError as e:
                logger.info(e)
                continue

            payload.append(BulkIReplaceDocumentSchema(replace=insert_stmt))

        data_to_post = "\n".join(document.json() for document in payload)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url=f"{BASE_URL}/bulk",
                content=data_to_post,
                headers={"Content-Type": "application/x-ndjson"},
            )
            if not response.status_code == 200:
                logger.error(response.json())

            else:
                logger.info(response.json())

        await asyncio.sleep(0.1)


async def make_search_request():
    must_stmt: list[dict] = [
        {
            "range": {"uploaded_at": {
                "gte": int(datetime.timestamp(datetime.now(tz=UTC) - timedelta(days=1)))
            }
            }},
        {"equals": {"is_blogger": random.randint(0, 1)}},
        {"in": {"any(source_id)": list(range(5))}}]

    should_stmt: list[dict] = []
    must_not_stmt: list[dict] = []

    for i in range(10):
        should_stmt.append({"query_string": f'"{lorem.words(1)}"'})
        must_not_stmt.append({"query_string": f'"some_exclude_words"'})

    query = {"bool": {"must": must_stmt}}

    if should_stmt:
        query["bool"]["must"].append({"bool": {"should": should_stmt}})

    if must_not_stmt:
        query["bool"]["must_not"] = must_not_stmt

    payload = RequestSearchSchema(
        index="posts_idx",
        sort=["posted"],
        offset=0,
        limit=10_000,
        query=query,
    )

    body = payload.dict(exclude_none=True)
    body["highlight"] = {"limit": 50_000}
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{BASE_URL}/search",
                json=body,
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(response.json())

            else:
                logger.info(f"Нашли {response.json()['hits']['total']}")

        await asyncio.sleep(0.1)


async def init_db():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f'{BASE_URL}/cli?{INDEX_STMT}')
        if r.status_code == 200:
            logger.info("Инициализировали Индекс")
        else:
            logger.error(r.json())


async def main():
    await asyncio.sleep(10)  # Ждем запуска мантикоры
    await init_db()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(insert_to_manticore())
        tg.create_task(make_search_request())


if __name__ == "__main__":
    asyncio.run(main())
