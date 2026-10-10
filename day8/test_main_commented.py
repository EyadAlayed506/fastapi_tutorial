# =============================================================================
# Day 8 - Testing: the tests  (commented copy of test_main.py)
#
# Run from the project root:
#     uv run pytest day8 -v
# pytest automatically collects files named test_*.py and functions named
# test_*, so this file runs too (the same checks as test_main.py).
# =============================================================================

# TestClient sends fake HTTP requests directly to the app - no real server,
# no network, no browser needed.
from fastapi.testclient import TestClient

# Import the app object we want to test. `main` is day8/main.py: pytest adds
# the test file's folder to Python's import path, so this import works.
from main import app

client = TestClient(app)  # app = the server being tested, client = the fake HTTP client


# Every function whose name starts with test_ is a test.
# Each `assert` must be True; the first False assert makes the test FAIL.
def test_any():
    # 1) Happy path with a query parameter.
    respone = client.get("/items/10?q=phone")
    assert respone.status_code == 200
    # .json() parses the response body into a Python dict.
    assert respone.json() == {
        "item_id": 10,  # the path "10" was converted to the int 10
        "q": "phone"
    }
    # 2) Optional query parameter left out -> q is None (null in JSON).
    respone2 = client.get("/items/10")
    assert respone2.status_code == 200
    assert respone2.json() == {
        "item_id": 10,
        "q": None
    }
    # 3) Error case: 0 breaks Path(ge=1) -> FastAPI answers 422 by itself.
    # Testing failures matters as much as testing successes.
    respone3 = client.get("/items/0")
    assert respone3.status_code == 422

# Tip from the Day 8 notes: splitting these three checks into three separate
# test functions (test_get_item, test_get_item_without_query,
# test_invalid_item_id) makes it obvious WHICH case broke when a test fails.
