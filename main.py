import os
from dotenv import load_dotenv
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.chat_models import ChatOpenAI

def get_loaders(path):
    """ Returns loaders for all the files in path"""
    loaders = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)

            if file.endswith('.txt'):
                loaders.append(TextLoader(file_path))
            elif file.endswith('.pdf'):
                loaders.append(PyPDFLoader(file_path))

    return loaders
    
def main():
    loaders = get_loaders("test/data/")
    index = VectorstoreIndexCreator().from_loaders(loaders)
    print(f"Number of sources: {len(loaders)}\n")

    llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")

    query = "What country did Sweden occupy during the second world war?"
    # query = "What is the protection degree of the Hypercharger 225?"

    #query = """What did USA do during the second world war? Answer in the following format: 
    #[{"action": <short descriprtion>, "date": <the date when the action occured>}, ...]
    #"""

    response = index.query_with_sources(query, llm=llm)
    response["answer"] = response["answer"].rstrip("\n") # Remove trailing newline character

    print(f"Question: {response['question']}")
    print(f"Answer: {response['answer']}")
    print(f"Sources: {response['sources']}")

# Standard practice. Makes it possible to import functions from this file without actually runnit it
if __name__ == "__main__":
    load_dotenv()
    main()