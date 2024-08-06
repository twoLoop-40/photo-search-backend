from collections.abc import AsyncGenerator
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends
from db.connect_db import connection
from db.db_settings import mongo_settings

app = FastAPI()


@app.get("/")
async def root(async_db: Annotated[AsyncGenerator, Depends(lambda: connection.get_db(mongo_settings.store_db))]):

    coll_str = mongo_settings.latex_source_coll
    async with async_db as db:
        coll = db[coll_str]
        count_document = await coll.aggregate([
            {"$count": "total_document"}
        ]).to_list(length=None)
        return {"message": count_document}
