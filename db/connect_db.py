import os

from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

load_dotenv()


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


connection = ConnectDB()
