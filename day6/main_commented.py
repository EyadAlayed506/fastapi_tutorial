# =============================================================================
# Day 6 - Dependencies: first steps & classes as dependencies
#         (commented copy of main.py)
#
# Run it from the project root:
#     uv run fastapi dev day6/main_commented.py
# =============================================================================

from typing import Annotated

# Depends -> marks a parameter as "FastAPI must compute this for me by
# calling the given function/class first" (dependency injection).
from fastapi import Depends, FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


# -----------------------------------------------------------------------------
# Part 1: a function as a dependency
# -----------------------------------------------------------------------------
# A dependency looks exactly like an endpoint function: FastAPI reads its
# parameters (q, skip, limit) from the request - here as query parameters -
# validates them, calls the function, and passes the RESULT to the endpoint.
async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


# A reusable type alias: "a dict produced by calling common_parameters".
# Note: Depends(common_parameters) - we pass the function, we do NOT call it
# (common_parameters() would be wrong). FastAPI calls it per request.
CommonsDep = Annotated[dict, Depends(common_parameters)]  # call function common_parameter anad pass it to commnsDep
# that prevent redudent code


# Request flow for GET /items/?q=foo&limit=5:
#   1. FastAPI sees the CommonsDep parameter
#   2. it reads q, skip, limit from the query string and validates them
#   3. it calls common_parameters(q="foo", skip=0, limit=5)
#   4. the returned dict is passed in as `commons`
#   5. the endpoint runs
@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons


# The same dependency reused by a second endpoint - no repeated parameters.
@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons


# -----------------------------------------------------------------------------
# Part 2: a class as a dependency
# -----------------------------------------------------------------------------
# we can do it with classes (more optimal than functions in this case)
#
# Why a class? A dict gives the editor no idea which keys exist. A class gives
# real attributes (commons.q, commons.skip) with autocomplete and type checks.
# FastAPI can use a class because classes are *callable*: calling
# common_parameters_class(...) creates an instance. FastAPI reads the
# __init__ parameters just like a function's parameters.
# (Convention tip: class names are usually CamelCase, e.g. CommonQueryParams.)
class common_parameters_class:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


# First part of Annotated = the type (for your editor).
# Depends(...)            = what FastAPI actually calls.
item_filtered = Annotated[common_parameters_class, Depends(common_parameters_class)]


@app.get("/items_class/")
# Note: this function has the same Python name as the first read_items.
# That is OK for FastAPI - the route was registered by the decorator before the
# name was reused - but unique function names are clearer.
async def read_items(commons: item_filtered):
    response = {}
    if commons.q:
        response.update({"q": commons.q})

    # List slicing for pagination: skip the first `skip` items, take `limit`.
    items = fake_items_db[commons.skip:commons.skip + commons.limit]
    response.update({"items": items})
    return response
