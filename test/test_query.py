from alphageist.query import query_files
from dotenv import load_dotenv

load_dotenv()

TEST_DATA_PATH = "test/data/"

def test_query_files_python():
    query = "What does the fucntion generate_random_prime(start, end) do?"
    res = query_files(query, TEST_DATA_PATH)
    assert res['sources'] == "test/data/code.py"

def test_query_files_csv():
    query = "Does Jonathan Jönsson have an employment number?"
    res = query_files(query, TEST_DATA_PATH)
    assert res['sources'] == "test/data/Employees_list.csv"

def test_query_files_txt():
    query = "What country did Sweden occupy during the second world war?"
    res = query_files(query, TEST_DATA_PATH)
    assert res['sources'] == "test/data/ww2/ww2.txt"

def test_query_files_pdf():
    query = "What is the protection degree of the Hypercharger 225?"
    res = query_files(query, TEST_DATA_PATH)
    assert res['sources'] == "test/data/HYC_225_300_produktbrief_v20180513.pdf"
      
