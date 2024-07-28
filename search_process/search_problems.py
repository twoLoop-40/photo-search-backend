import re
from collections.abc import Callable
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, Field, ConfigDict

from concept_graph.vector_query import VectorQuery

image_mark = r'<!-- image -->'


def paste_description(math_problem: str, image_descriptions: list[str]) -> str:
    # help func
    def replacer(match, descriptions=None):
        # 초기화
        if descriptions is None:
            descriptions = image_descriptions

        if replacer.counter < len(descriptions):
            description = f'<그림 {replacer.counter + 1}: {descriptions[replacer.counter]}'
            replacer.counter += 1
            return description
        return match.group(0)

    replacer.counter = 0

    # use re.sub
    result = re.sub(image_mark, replacer, math_problem)

    return result


AssociateImage = Callable[[str, dict[str, str]], str]


class SearchProblem(BaseModel):
    math_problem: str | None = None
    image_descriptions: list[str] = Field(default=[])
    refined_math_problem: str | None = None
    vector: list[float] = Field(default=[])

    def associate_image(self, associate: AssociateImage) -> str:
        refined_math_problem = self.refined_math_problem

        # check if it exists
        if refined_math_problem:
            return refined_math_problem

        math_problem = self.math_problem
        image_descriptions = self.image_descriptions

        associate_result = associate(math_problem, image_descriptions)
        if associate_result:
            self.refined_math_problem = associate_result
            return associate_result

        else:
            self.refined_math_problem = math_problem
            return math_problem

    def conjure_vector(self, embedder, associate_image: Optional[AssociateImage] = paste_description):
        if self.vector and len(self.vector) > 0:
            return self.vector

        refined_math_problem = self.refined_math_problem
        if refined_math_problem is None:
            print(f"refined math problem is None")
            if associate_image is None:
                print("failed to associate image")
                return

            self.associate_image(associate=associate_image)
            return self.conjure_vector(embedder)

        vector_embedded = embedder(refined_math_problem)

        self.vector = vector_embedded

        return vector_embedded


class SearchType(Enum):
    PROBLEM = 'problem'
    QUESTION = 'question'
    SOLUTION = 'solution'


class QueryType(Enum):
    PROBLEM = 'problemEmbedding'
    QUESTION = 'questionEmbedding'
    SOLUTION = 'solutionEmbedding'


class IndexType(Enum):
    PROBLEM = 'problem_index'
    QUESTION = 'question_index'
    SOLUTION = 'solution_index'


class ProblemQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, validate_default=True,
                              use_enum_values=True)

    query_type: QueryType | None = None
    index_type: IndexType | None = None

    vector_query: VectorQuery | None = None
    search_problem: SearchProblem | None = None

    def _verify_type(self, type_value: SearchType):
        # print(f"type_value: {type_value}")
        if type_value == SearchType.PROBLEM.value:
            self.query_type = QueryType.PROBLEM.value
            self.index_type = IndexType.PROBLEM.value
        if type_value == SearchType.QUESTION.value:
            self.query_type = QueryType.QUESTION.value
            self.index_type = IndexType.QUESTION.value
        if type_value == SearchType.SOLUTION.value:
            self.query_type = QueryType.SOLUTION.value
            self.index_type = IndexType.SOLUTION.value

    def search_similar_problems(self, type_value: SearchType):
        search_problem = self.search_problem
        vector_query = self.vector_query
        if self.query_type is None or self.index_type is None:
            self._verify_type(type_value)
            vector_query.index = self.index_type
            vector_query.path = self.query_type

        embedder = vector_query.embeddings.embed_query
        vector = search_problem.conjure_vector(embedder=embedder)
        query = search_problem.refined_math_problem

        unset_fields = ['problemEmbedding', 'questionEmbedding', 'solutionEmbedding', 'descriptionEmbedding',
                        'problemSummary', 'questionSummary', 'solutionSummary', '_id', 'school', 'year',
                        'conceptDescription']

        # print(f"index: {vector_query.index}")
        # print(f"path: {vector_query.path}")
        retrieved_results = vector_query.content_retriever(query=query, vector=vector, remove_fields=unset_fields)

        return retrieved_results
