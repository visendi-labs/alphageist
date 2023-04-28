import time
import sys
import threading  
from alphageist.query import query_vectorstore
from alphageist.vectorstore import get_vectorstore
from langchain.vectorstores.base import VectorStore
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"

class CLI:
    vectorstore: VectorStore
    __vs_thread: threading.Thread
    def __init__(self, path):
        self.__vs_thread = threading.Thread(target=self._get_vectorstore, args=(path,))
        self.__vs_thread.start()

    def _get_vectorstore(self, path):
       self.vectorstore = get_vectorstore(path) 

    def run(self):
        print("Loading vectorstore", end='')
        cnt = 1
        while self.__vs_thread.is_alive():
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