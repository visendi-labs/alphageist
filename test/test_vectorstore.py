from os import path
import pytest
from alphageist.vectorstore import create_vectorstore

def test_get_docs_from_file_non_existing():
    with pytest.raises(ValueError) as exc_info:
        create_vectorstore(path.join("test", "data", "empty_folder"), ".")