from alphageist.query import query_docs
from alphageist.doc_generator import get_docs_from_drive
from dotenv import load_dotenv

TEST_DATA_PATH = "test/data"

def main():

    path = input("Path (test/data/):")
    path = path if path else TEST_DATA_PATH

    docs = get_docs_from_drive(path)        
    
    while query := input("Query: "):
        response = query_docs(docs, query) 

        print(f"Question: {response['question']}")
        print(f"Answer: {response['answer']}")
        print(f"Sources: {response['sources']}\n")

# Standard practice. Makes it possible to import functions from this file without actually runnit it
if __name__ == "__main__":
    load_dotenv()
    main()