# =============================================================================
# Day 2 - Path Parameters & Numeric Validations / Query Parameters & String
#         Validations  (commented copy of main.py)
#
# Run it from the project root:
#     uv run fastapi dev day2/main_commented.py
# Then open http://127.0.0.1:8000/docs and try the four test cases below.
# =============================================================================

# FastAPI -> the class that creates the application.
# Path    -> adds validation rules + docs metadata to a *path* parameter.
# Query   -> adds validation rules + docs metadata to a *query* parameter.
from fastapi import FastAPI, Path, Query

# Annotated[type, extra_info] lets us attach extra information (here: the
# Path/Query rules) to a normal type hint. Python itself ignores the extra
# info, but FastAPI reads it. This is the recommended modern style.
from typing import Annotated

# Creating the app object. `fastapi dev` looks for a variable called `app`.
app = FastAPI()

# TODO 1: GET /items/{item_id}
# item_id: Annotated[int, Path(gt=0, le=1000)]
# -> must be a positive integer, max 1000
# q: Annotated[str | None, Query(min_length=3, max_length=50)] = None
# -> optional, but if given, must be 3-50 characters

# return {"item_id": item_id, "q": q}
# TODO 2: test all four cases below in /docs and note what happens to each:
# a) /items/5 (valid item_id, no q)
# b) /items/0 (invalid - violates gt=0)
# c) /items/5?q=hi (invalid - q too short, violat
#
# (The original TODO list was cut off here. From the Day 2 summary PDF:
#  c) /items/5?q=hi     -> invalid, q too short (min_length=3)
#  d) /items/5?q=hello  -> valid, passes both checks)


# The decorator registers this function for GET requests whose URL matches
# "/items/{item_id}". The part in curly braces is a *path parameter*: whatever
# the client puts there is passed to the function argument with the same name.
@app.get("/items/{item_id}")
async def get_item_id(
    # item_id appears in the path string, so FastAPI treats it as a path
    # parameter. Path parameters are ALWAYS required (they are part of the URL).
    #   int          -> "5" from the URL is converted to the integer 5;
    #                   "abc" is rejected with 422 before the function runs.
    #   gt=0         -> greater than 0      (so 0 and negatives are rejected)
    #   le=1000      -> less than or equal to 1000
    item_id: Annotated[int, Path(gt=0, le=1000)],
    # q is NOT in the path string, so FastAPI treats it as a *query* parameter
    # (the ?q=... part of the URL).
    #   str | None   -> it may be missing
    #   = None       -> the default value; this is what makes q optional
    #   min_length / max_length -> only checked when q is actually sent
    q: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
):
    # If we reach this line, ALL validation has already passed.
    # Invalid requests never reach your code: FastAPI answers them with
    # 422 Unprocessable Entity and a JSON error naming the field and the rule.
    #
    # Note: the TODO suggested the key "item_id"; this solution uses "id".
    # Both are fine - it only changes the name of the key in the JSON response.
    #
    # Returning a dict -> FastAPI converts it to JSON automatically.
    return {"id": item_id,
            "q": q}
