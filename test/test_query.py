from functools import lru_cache
from alphageist.query import query_docs
from alphageist.doc_generator import get_docs_from_path
from dotenv import load_dotenv

load_dotenv()

TEST_DATA_PATH = "test/data/"

@lru_cache(maxsize=None)
def _get_test_docs():
    return get_docs_from_path(TEST_DATA_PATH)

def test_query_docs_python():
    query = "What does the fucntion generate_random_prime(start, end) do?"
    res = query_docs(_get_test_docs(), query)
    assert res['sources'] == "test/data/code.py"

def test_query_docs_csv():
    query = "Does Jonathan Jönsson have an employment number?"
    res = query_docs(_get_test_docs(), query)
    assert res['sources'] == "test/data/Employees_list.csv"

def test_query_docs_txt():
    query = "What country did Sweden occupy during the second world war?"
    res = query_docs(_get_test_docs(), query)
    assert res['sources'] == "test/data/ww2/ww2.txt"

def test_query_docs_pdf():
    query = "What is the protection degree of the Hypercharger 225?"
    res = query_docs(_get_test_docs(), query)
    assert res['sources'] == "test/data/HYC_225_300_produktbrief_v20180513.pdf"
      
