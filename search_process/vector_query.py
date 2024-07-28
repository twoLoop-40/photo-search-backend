from dotenv import load_dotenv
import os

from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from db.db_basics import ConnectionDB
from db.queries import find_by_aggregation

load_dotenv()

openai_embedding_option = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "model": "text-embedding-3-large"
}


class VectorQuery(BaseModel):
    embeddings: OpenAIEmbeddings = Field(default_factory=lambda: OpenAIEmbeddings(**openai_embedding_option))
    num_candidates: int = Field(default=300)
    index: str = Field(default="concepts_2015_embedding")
    filters: dict | None = Field(default=None)
    path: str = Field(default='conceptEmbedding')
    db_name: str = Field(default="math_concepts")
    coll_name: str = Field(default="concepts_2015")

    def content_retriever(self, query: str, vector: list[float] | None = None, score_limit=0.5, limit=20,
                          remove_fields: list[str] | None = None):
        embeddings = self.embeddings
        num_candidates = self.num_candidates
        index = self.index
        filters = self.filters
        path = self.path

        if remove_fields is None:
            remove_fields = ["conceptEmbedding", "score"]
        query_vector = vector if vector is not None else embeddings.embed_query(query)
        pipeline = [
            {"$vectorSearch": {
                "index": index,
                "path": path,
                "queryVector": query_vector,
                "numCandidates": num_candidates,
                "limit": limit,
                "filter": filters if filters else {}

            }},
            {"$set": {"score": {"$meta": "vectorSearchScore"}}},
            {"$set": {"_id": {"$toString": "$_id"}}},
            {"$match": {"score": {"$gte": score_limit}}},
            {"$sort": {"score": -1}},
            {"$unset": remove_fields}
        ]
        db_name = self.db_name
        coll_name = self.coll_name

        connection = ConnectionDB(db_name=db_name, coll_name=coll_name)

        result_contents = connection.execute_query(find_by_aggregation, pipeline)
        return result_contents


if __name__ == "__main__":
    def test_vector_query():
        query = r"""
         이 문제는 직사각형의 성질, 중점, 원의 접선, 삼각함수 등을 이용한 문제입니다.
         먼저 직사각형 $ABCD$의 변의 길이를 이용하여 중점 $E$와 $F$의 좌표를 구합니다. 
         그 다음, 점 $P$가 선분 $BC$ 위에 있을 때, 직선 $AP$가 원과 접한다는 조건을 이용하여 $\theta$를 구합니다. 
         마지막으로 $\theta$의 사인 값을 구하여 주어진 형태로 표현한 후, $30(p+q)$의 값을 계산합니다.    
        """
        concept_query = VectorQuery()
        result = concept_query.content_retriever(query, score_limit=0.5)
        print(result)


    test_vector_query()
