from pydantic import BaseModel


class MongoDBSettings(BaseModel):
    store_db: str = 'keep_go1ng_store'
    latex_source_coll: str = 'latex_source'


mongo_settings = MongoDBSettings()
