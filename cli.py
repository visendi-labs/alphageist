import time
import sys
import threading  
from alphageist.query import query_vectorstore
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from langchain.vectorstores.base import VectorStore
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"
PERSIST_DIRECTORY = ".alphageist"

class CLI:
    vectorstore: VectorStore
    _loading_vectorstore: bool = False
    def __init__(self, path):
        if vectorstore_exists(PERSIST_DIRECTORY):
            self.vectorstore = load_vectorstore(PERSIST_DIRECTORY)
        else:
            self._loading_vectorstore = True
            threading.Thread(target=self._create_vectorstore, args=(path,PERSIST_DIRECTORY)).start()

    def _create_vectorstore(self, path, persist_vectorstore):
       self.vectorstore = create_vectorstore(path, persist_vectorstore) 
       self._loading_vectorstore = False

    def run(self):
        print("Loading vectorstore", end='')
        cnt = 1
        while self._loading_vectorstore:
            sys.stdout.write(".")
            time.sleep(0.2)
            if cnt%4 == 0:
                sys.stdout.write(4*"\b")
                sys.stdout.write(4*" ")
                sys.stdout.write(4*"\b")
            sys.stdout.flush()
            cnt = cnt + 1
        print("")

        while query := input("Query: "):
            response = query_vectorstore(self.vectorstore, query) 

            print(f"Question: {response['question']}")
            print(f"Answer: {response['answer']}")
            print(f"Sources: {response['sources']}\n")
   

def main():
    path = input("Path (test/data/):")
    path = path if path else TEST_DATA_PATH

    client = CLI(path)
    client.run() 

# Standard practice. Makes it possible to import functions from this file without actually runnit it
if __name__ == "__main__":
    load_dotenv()
    main()