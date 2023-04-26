import os
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PythonLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.chat_models import ChatOpenAI


def get_loaders2(path):
    return [DirectoryLoader(path,glob="**/*.csv", loader_cls=CSVLoader)]

def get_loaders(path):
    loaders = []
    for root, dirs, files in os.walk(path):
         for file in files:
             file_path = os.path.join(root, file)

             if file.endswith('.txt'):
                 loaders.append(TextLoader(file_path))
             elif file.endswith('.pdf'):
                 loaders.append(PyPDFLoader(file_path))
             elif file.endswith('.csv'):
                 loaders.append(CSVLoader(file_path))  
             elif file.endswith('.py'):
                 loaders.append(PythonLoader(file_path))
             elif file.endswith('.jpeg') or file.endswith('.png'):
                loaders.append(UnstructuredImageLoader(file_path))

    return loaders

def query_files(query: str, path: str):
    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
    loaders = get_loaders(path)
    if len(loaders) == 0:
        raise Exception("error: no loaders found")

    print(f"Number of loaders: {len(loaders)}\n")
    index = VectorstoreIndexCreator().from_loaders(loaders)

    response = index.query_with_sources(query, llm=llm)
    response["answer"] = response["answer"].rstrip("\n") # Remove trailing newline character

    return response