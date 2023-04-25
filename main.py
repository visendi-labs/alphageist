from alphageist.dir_query import query_files
from dotenv import load_dotenv

def main():

    while True:
        query = input("Query: ")

        response = query_files(query, "test/data/")

        print(f"Question: {response['question']}")
        print(f"Answer: {response['answer']}")
        print(f"Sources: {response['sources']}\n")

# Standard practice. Makes it possible to import functions from this file without actually runnit it
if __name__ == "__main__":
    load_dotenv()
    main()