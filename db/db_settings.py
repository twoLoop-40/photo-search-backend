from pydantic import BaseModel


class MongoDBSettings(BaseModel):
    store_db: str = 'keep_go1ng_store'
    concept_db: str = 'concepts_2015_embedding'
    latex_source_coll: str = 'latex_source'


mongo_settings = MongoDBSettings()
