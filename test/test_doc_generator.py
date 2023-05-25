import pytest
from os import path
from alphageist.doc_generator import get_docs_from_file

@pytest.mark.parametrize("filepath, expected_n_docs", [
    (path.join("test", "data", "ww2", "ww2.txt"), 146),
    (path.join("test", "data", "Employees_list.csv"), 26),
    (path.join("test", "data", "code.py"), 1),
    (path.join("test", "data", "lithium_ion_battery_degradation_report.pdf"), 141),
    (path.join("test", "data", "volvo q3 -22 summary.docx"), 2),
    (path.join("test", "data", "spotify1.jpeg"), 0), # Not supported should return 0
])
def test_get_docs_from_file(filepath:int, expected_n_docs:int):
    res = get_docs_from_file(filepath)
    assert len(res) == expected_n_docs

def test_get_docs_from_file_non_existing():
    with pytest.raises(ValueError) as exc_info:
        get_docs_from_file("non_existing_filepath.pdf")
    
