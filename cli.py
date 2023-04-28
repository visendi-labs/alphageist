import time
import sys
import threading  
from alphageist.query import query_docs
from alphageist.doc_generator import get_docs_from_path
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"

class CLI:
    __docs = []
    __docs_thread: threading.Thread
    def __init__(self, path):
        self.__docs_thread = threading.Thread(target=get_docs_from_path, args=(path, self.__docs))
        self.__docs_thread.start()

    def run(self):
        print("Loading docs", end='')
        cnt = 1
        while self.__docs_thread.is_alive():
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
            response = query_docs(self.__docs, query) 

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