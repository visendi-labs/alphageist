import os
import logging
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.chroma import Chroma
from alphageist.doc_generator import get_docs_from_path
from alphageist.errors import MissingConfigComponentError
from alphageist import util
import alphageist.config as cfg


def vectorstore_exists(persist_directory: str) -> bool:
    """This function checks if the vectorstore already 
    exists at the specified directory"""
    return os.path.exists(persist_directory)


def get_embeddings(config: dict) -> Embeddings:
    """This function returns the proper Embeddings according
    to the config"""
    if not cfg.API_KEY_OPEN_AI in config.keys():
        raise MissingConfigComponentError(cfg.API_KEY_OPEN_AI)
    return OpenAIEmbeddings(openai_api_key=config[cfg.API_KEY_OPEN_AI])


def app_support_dir(config: dict) -> str:
    """This function returna the application support 
    directory based on the operating system"""
    if not cfg.VECTORDB_DIR in config.keys():
        raise MissingConfigComponentError(cfg.VECTORDB_DIR)
    vector_db_dir = config[cfg.VECTORDB_DIR]
    if not vector_db_dir:
        raise ValueError(f"Path for persisting db cannot be empty")

    if os.name == 'nt':  # If the OS is Windows, use the APPDATA environment variable
        app_data_path = os.getenv('APPDATA')
        app_support_path = os.path.join(app_data_path, "Visendi Assistant", vector_db_dir)
    else:  # Assume that it is macOS or Linux, use the user's Library/Application Support directory
        app_support_path = os.path.expanduser("~/Library/Application Support/Visendi Assistant/" + vector_db_dir)

    os.makedirs(app_support_path, exist_ok=True)
    if not util.path_is_valid_format(app_support_path):
        raise ValueError(f'"{app_support_path}" is not a valid directory')
    return app_support_path


def load_vectorstore(config: dict) -> Chroma:
    """This function loads the vectorstore from the specified directory"""
    embedding = get_embeddings(config)
    vector_db_dir = app_support_dir(config)
    logging.info(f"Loading vectorstore from {vector_db_dir}...")
    client = Chroma(embedding_function=embedding, persist_directory=vector_db_dir)
    return client


def create_vectorstore(config: dict) -> Chroma:
    """This function creates the vectorstore from 
    the documents found in the specified directory"""
    if not cfg.SEARCH_DIRS in config.keys():
        raise MissingConfigComponentError(cfg.SEARCH_DIRS)

    search_dir = config[cfg.SEARCH_DIRS]
    if not util.path_is_valid_format(search_dir):
        raise ValueError(f"{search_dir} is not a valid directory")

    docs = get_docs_from_path(search_dir)

    if not docs:
        raise ValueError(f"No supported files found in {search_dir}")

    vector_db_dir = app_support_dir(config)

    embedding = get_embeddings(config)
    logging.info(f"Creating vectorstore...")
    client = Chroma.from_documents(docs, embedding=embedding, persist_directory=vector_db_dir)
    logging.info(f"Saving vectorstore to {vector_db_dir}")
    client.persist() # Save DB
    return client