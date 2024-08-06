from motor.motor_asyncio import AsyncIOMotorCollection


async def find_by_aggregation(coll: AsyncIOMotorCollection, pipeline: list[dict]):
    query_result = await coll.aggregate(pipeline=pipeline).to_list(length=None)
    return query_result
