import time
import sys
import threading  
from alphageist.query import query_vectorstore
from alphageist.vectorstore import create_vectorstore, vectorstore_exists, load_vectorstore
from langchain.vectorstores.base import VectorStore
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"
PERSIST_DIRECTORY = ".alphageist"
class CLIStreamHandler(StreamingStdOutCallbackHandler):
    
    def __init__(self):
        super().__init__()
        self.muted:bool = False
        self.response: str = ""

    def on_llm_new_token(self, token: str, **kwargs):
        """Run on new LLM token. Only available when streaming is enabled."""
        # The prompt is always finished by: SOURCES: <sources>, hence we want to 
        # stop printing when we get this. SOURCES comes in two different tokens:
        # [S] + [OURCES]. Since many other words starts with S we have to wait until
        # we se OURCES before we can act`
        if token == "OURCES" and self.response[-1] == "S":
            self.muted = True
            sys.stdout.write("\b ")
            sys.stdout.flush()

        if self.muted:
            return

        self.response = self.response + token
        sys.stdout.write(token)
        sys.stdout.flush()

    def on_llm_end(self, response, **kwargs) -> None:
        """Run when LLM ends running."""
        print("")
        self.response = ""
        self.muted = False

        
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
            response = query_vectorstore(self.vectorstore, query, callbacks=[CLIStreamHandler()]) 

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