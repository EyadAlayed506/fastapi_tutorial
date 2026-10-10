# =============================================================================
# Day 7 - Dependencies with yield & sub-dependencies (setup / teardown order)
#         (commented copy of main.py)
#
# Run it from the project root:
#     uv run fastapi dev day7/main_commented.py
# then open http://127.0.0.1:8000/test/ and watch the TERMINAL output.
# =============================================================================

from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()


# Dependency A
# A dependency that uses `yield` instead of `return` has two halves:
#   - code BEFORE yield  -> setup    (e.g. open a database connection)
#   - the yielded value  -> what gets injected into whoever depends on it
#   - code AFTER yield   -> teardown (e.g. close the connection)
# FastAPI runs the teardown after the response has been produced.
async def get_resource():
    print("A open")
    try:
        yield "conn -1"
    finally:
        # `finally` runs no matter what - even if the endpoint raised an
        # error - so the resource is always cleaned up.
        print("A close")


# Dependency B depends on A  (a *sub-dependency*)
# FastAPI must run A first to get `resource`, then it can start B.
async def get_sub(
    resource: Annotated[str, Depends(get_resource)]
):
    print("B open")
    try:
        yield f"sub using {resource}"
    finally:
        print("B close")


# Path operation
# The endpoint only asks for B. FastAPI discovers that B needs A and resolves
# the whole chain automatically.
# Note: this is a normal `def` while the dependencies are `async def` -
# FastAPI allows mixing the two.
@app.get("/test/")
def get_value(
    value: Annotated[str, Depends(get_sub)]
):
    print("endpoint")
    return value

# a open
# b open
# endpoint
# return sub using conn1
# b close
# a close
#
# Why this order? Setup runs from the innermost dependency outwards
# (A, then B, then the endpoint). Teardown runs in REVERSE (B closes before A),
# like stacked boxes: the last one opened is the first one closed. B is still
# using A's resource, so A must stay open until B has finished.
# (The response body is "sub using conn -1" - the yielded string has a space
# and a dash: "conn -1".)
