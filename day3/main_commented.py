# =============================================================================
# Day 3 - Query parameter models & nested request-body models
#         (commented copy of main.py)
#
# Run it from the project root:
#     uv run fastapi dev day3/main_commented.py
# =============================================================================

# Literal["a", "b"] -> a type that only allows these exact values.
from typing import Annotated, Literal

from fastapi import FastAPI, Query

# BaseModel -> the parent class of every Pydantic model (a typed "data shape").
# Field     -> adds defaults, validation rules and docs metadata to a model field
#              (it is the model-field equivalent of Query()/Path()).
# HttpUrl   -> a special type that only accepts a valid http/https URL.
from pydantic import BaseModel, Field, HttpUrl

app = FastAPI()


# -----------------------------------------------------------------------------
# Part 1: grouping several query parameters into one Pydantic model
# -----------------------------------------------------------------------------
# Instead of writing limit, offset, order_by and tags as four separate function
# parameters, we describe them once in a class. This keeps endpoints short and
# lets several endpoints reuse the same set of query parameters.
class FilterParams(BaseModel):
    # "extra": "forbid" -> any query parameter that is NOT declared below is
    # rejected with 422. e.g. /items/?limit=5&color=red fails because of "color".
    model_config = {"extra": "forbid"}

    # Field(100, ...) -> the first argument is the default value (100).
    #   gt=0, le=100 -> must be 1..100. (The description text says "0-100", but
    #   gt=0 means 0 itself is NOT allowed.)
    limit: int = Field(100, gt=0, le=100, description="limite must be between 0-100")  # u can use query(...) isntead
    # ge=0 -> greater than or equal to 0. title= only shows up in the docs.
    offset: int = Field(0, ge=0, title="offset")
    # Only these two strings are accepted; anything else -> 422.
    order_by: Literal["created_at", "updated_at"] = "created_at"
    # either of them default created_at
    # A list in a query model means the parameter can be repeated:
    #   /items/?tags=a&tags=b  ->  tags == ["a", "b"]
    tags: list[str] = []


@app.get("/items/")
# Annotated[FilterParams, Query()] tells FastAPI: "build a FilterParams object,
# but read its fields from the QUERY STRING, not from the request body".
# Without Query(), a Pydantic model parameter would be treated as a JSON body.
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    # take the values from query
    # filter_query is a real FilterParams object here (already validated).
    # Returning a Pydantic model -> FastAPI turns it into JSON for us.
    return filter_query


# -----------------------------------------------------------------------------
# Part 2: nested models in a request body
# -----------------------------------------------------------------------------
class Image(BaseModel):
    url: HttpUrl  # gives an error if it is invalid ("hello" -> 422)
    name: str


class Item(BaseModel):
    name: str                         # required (no default)
    description: str | None = None    # optional
    price: float                      # required
    tax: float | None = None          # optional
    # set[str] -> duplicates are removed automatically:
    #   ["a", "a", "b"] in the JSON becomes {"a", "b"}
    tags: set[str] = set()
    # A model used as the type of a field = a *nested* model.
    # The JSON body may contain an "image": {"url": ..., "name": ...} object,
    # and Pydantic validates it with the Image rules above.
    image: Image | None = None


@app.put("/items/{item_id}")
# FastAPI decides where each parameter comes from:
#   item_id  -> appears in the path          -> path parameter
#   item     -> its type is a Pydantic model -> JSON request body
async def update_item(item_id: int, item: Item):
    results = {"item_id": item_id, "item": item}
    return results
