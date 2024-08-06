import os
from collections.abc import Callable, Coroutine

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

load_dotenv()

Pipelines = list[dict]
AggregationResults = list[dict]
ExecuteAggregation = Callable[[str, str, Pipelines], Coroutine[None, None, AggregationResults]]
ProcessQuery = Callable[[AsyncIOMotorCollection, Pipelines], Coroutine[None, None, AggregationResults]]


class ConnectDB(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    db_uri: str = Field(default=os.getenv('MONGO_URI'))

    @asynccontextmanager
    async def client_up(self):
        client = None
        try:
            print('Connecting to MongoDB...')
            client = AsyncIOMotorClient(self.db_uri)
            yield client

        finally:
            if client:
                client.close()

    @asynccontextmanager
    async def get_db(self, db_name: str):
        async with self.client_up() as client:
            db = client[db_name]
            yield db

    def execute_query(self, proceed_query: ProcessQuery) -> ExecuteAggregation:
        async def executor(db_name: str, coll_name: str, pipelines: Pipelines) -> AggregationResults:
            async with self.get_db(db_name) as db:
                coll = db[coll_name]
                return await proceed_query(coll, pipelines)

        return executor


connection = ConnectDB()
