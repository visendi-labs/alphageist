from langchain.docstore.document import Document
from langchain.vectorstores.base import VectorStoreRetriever, VectorStore 
from langchain.schema.retriever import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun

from langchain.pydantic_v1 import Field, root_validator

class MultiStoreRetreiver(BaseRetriever):
    """Merges the result from multiple vector stores and re-ranks 
    them by relevance score"""

    vectorstores: list[VectorStore]
    """The vectorstores that will be queried"""
    k:int = 4
    """Number of results to return. The vectorstores that are queried should return minimum this amount"""
    search_kwargs: dict = Field(default_factory=dict)
    """Keyword arguments to pass to the search functions."""
    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
        ) -> list[Document]:
        # Merge results from all stores
        scored_docs = [] # [(<Document>, <score_float>)]
        for vs in self.vectorstores:
            scored_docs.extend(vs.similarity_search_with_relevance_scores(query, k=self.k, **self.search_kwargs))
        
        # Sort the result
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        docs = [doc for doc, _ in scored_docs][:self.k]

        return docs

    def _aget_relevant_documents(*args, **kwargs):
        raise NotImplementedError
