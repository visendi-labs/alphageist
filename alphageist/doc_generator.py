import os 
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PythonLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter


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

def get_docs_from_drive(path):
    docs = []
    for loader in get_loaders(path):
        docs.extend(loader.load())

    print(f"Number of docs: {len(docs)}")

    subdocs = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=0).split_documents(docs)
    print(f"Number of subdocs: {len(subdocs)}")

    return subdocs
 