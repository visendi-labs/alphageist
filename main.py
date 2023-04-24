from dotenv import load_dotenv
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import TextLoader
from langchain.llms import OpenAI

# Returns loaders for all the files in path
def get_loaders(path):
    # TODO: Iterate through path and generate loaders
    loaders = []
    loaders.append(TextLoader(path + 'ww2.txt'))
    return loaders

def main():
    index = VectorstoreIndexCreator().from_loaders(get_loaders("test/data/"))

    llm = OpenAI(temperature=0.0, model_name="gpt-3.5-turbo")

    query = """What did USA do during the second world war? Answer in the following format: 
    [{"action": <short descriprtion>, "date": <the date when the action occured>}, ...]

    """
    print(index.query(query, llm=llm))

# Standard practice. Makes it possible to import functions from this file without actually runnit it
if __name__ == "__main__":
    load_dotenv()
    main()