from dotenv import load_dotenv
from langchain.indexes import VectorstoreIndexCreator
from langchain.document_loaders import TextLoader
from langchain.llms import OpenAI

load_dotenv()

loader = TextLoader('test/data/ww2.txt')

index = VectorstoreIndexCreator().from_loaders([loader])

llm = OpenAI(temperature=0.0, model_name="gpt-3.5-turbo")

query = """What did USA do during the second world war? Answer in the following format: 
[{"action": <short descriprtion>, "date": <the date when the action occured>}, ...]

"""
print(index.query(query, llm=llm))