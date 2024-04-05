import re
import sys
import logging
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.callbacks.base import BaseCallbackHandler

from alphageist.vectorstore import VectorStore
from alphageist import config as cfg

def get_sources_from_answer(answer: str) -> list[str]:
        if re.search(r"SOURCES:\s", answer):
            _, sources = re.split(r"SOURCES:\s", answer)
        else:
            sources = ""
        return sources.split(',')

