# =============================================================================
# Day 4 - Response models, status codes, path operation configuration
# Day 5 - Handling errors & body updates
#         (commented copy of main.py)
#
# Run it from the project root:
#     uv run fastapi dev day4-5/main_commented.py
# =============================================================================

from typing import Any

# jsonable_encoder converts Pydantic models (and dates, sets, ...) into plain
# JSON-compatible Python data (dicts, lists, str, int, ...). We use it before
# storing data in our fake "database" dictionary.
from fastapi.encoders import jsonable_encoder

# status         -> named constants for HTTP codes (status.HTTP_404_NOT_FOUND)
# HTTPException  -> an exception FastAPI turns into an HTTP error response
# Request        -> the raw incoming request (needed by exception handlers)
from fastapi import FastAPI, status, HTTPException, Request

# EmailStr -> a str that must look like an email (needs pydantic[email]).
from pydantic import BaseModel, EmailStr

# JSONResponse -> build a response yourself (status code + JSON content).
from fastapi.responses import JSONResponse

app = FastAPI()


# =============================================================================
# DAY 4 - Response model: never leak the password
# =============================================================================
# Version 1: two independent models.
#   UserIn  = what the client SENDS   (includes the password)
#   UserOut = what the API RETURNS    (no password)
class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


# @app.post("/user/", response_model=UserOut)
# async def create_user(user: UserIn) -> Any:
#     return user

# the password will be shown in the ouput (bad)
#
# Mentor note: with response_model=UserOut the password would actually be
# FILTERED OUT - response_model wins over the "-> Any" return type, and FastAPI
# keeps only UserOut's fields. The password leaks only if you return `user`
# with NO response_model and NO return type (or with return type UserIn).


# better way
#
# Version 2: inheritance. UserIn = every UserOut field + password.
# Shared fields are written once, so the two models can't drift apart.
#
# Mentor note: this file now defines UserIn and UserOut a SECOND time. Python
# simply rebinds the names to the newest class. Because `class UserIn(UserOut)`
# runs BEFORE the second UserOut is created, this UserIn inherits from the FIRST
# UserOut. It works here because both UserOut versions are identical, but in a
# real project keep one definition per model (or split versions into files).
class UserIn(UserOut):
    password: str


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


# Path operation configuration: everything in the decorator below changes how
# the endpoint behaves or how it appears in /docs - not the function logic.
@app.post("/user/", status_code=status.HTTP_200_OK, tags=["user"],
          # status_code -> the code sent on success. For "create" endpoints
          #                201 Created (status.HTTP_201_CREATED) is the usual
          #                choice; 200 also works.
          # tags        -> groups endpoints under a heading in /docs.
          # summary / description -> short title / long text in /docs.
          summary="create a user", description=
          """
        creating a post using these info (username,email,fullname)
"""
          # response_description -> describes the successful response in /docs.
          , response_description="The created user"
          # Don't build new code around it; migrate to the newer endpoint when possible.
          # (That is the meaning of deprecated=True - not used here.)
          )
# tag makes documentation better
# we can use response_model
#
# The return type `-> UserOut` acts as the response model:
#   1. the function returns `user` (a UserIn, which has a password),
#   2. FastAPI validates/filters it through UserOut,
#   3. only username, email and full_name are sent - the password is dropped.
async def create_user(user: UserIn) -> UserOut:
    return user


# =============================================================================
# DAY 5 - Handling errors
# =============================================================================
items = {"foo": "The Foo Wrestlers"}


# A custom exception is just a normal Python exception class.
# It stores the id so the handler can mention it in the message.
class new_exception(Exception):
    def __init__(self, id):
        self.id = id


# @app.exception_handler(X) -> "whenever exception X is raised anywhere in the
# app, call this function to build the response". The handler receives the
# request and the exception object.
@app.exception_handler(new_exception)
async def new_exception_handler(request: Request, exc: new_exception):
    return JSONResponse(
        # Mentor note: 401 means "Unauthorized" (not logged in). For an item
        # that does not exist, 404 Not Found is the correct code.
        status_code=401,
        content=f"sorry but we can not find item_id {exc.id}"
    )


@app.get("/items/{item_id}", tags=["items"])
async def read_item(item_id: str):
    if item_id not in items:
        # `raise`, not `return`: raising stops the function immediately and
        # FastAPI hands the exception to the matching handler above.
        raise new_exception(item_id)
    # Note: `items` is looked up when a REQUEST arrives, not when this function
    # is defined. By then the dictionary below has replaced the one above, so
    # /items/foo returns {"item": {"name": "Foo", "price": 50.2}}.
    return {"item": items[item_id]}


# =============================================================================
# DAY 5 - Body updates (partial update with exclude_unset + model_copy)
# =============================================================================
# Our fake database. It REPLACES the `items` dict defined above.
items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}


# Every field has a default, so the client may send only some of them.
class Item(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    tax: float = 10.5
    tags: list[str] = []


@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item) -> Item:  # we are taking itemid and update its values using item
    if item_id not in items:
        # The built-in way to send an error: FastAPI turns this into
        # status 404 with the JSON body {"detail": "..."}.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f" {item_id} was not found in the system"
        )
    # item_id is the one we want to change
    # item is the one with the updated values
    org_item = items[item_id]  # type of org_item is dic
    # new item without default values and type convert dict becasue(model_copy=dict)

    # exclude_unset=True -> keep ONLY the fields the client actually sent.
    # Without it, unsent fields would come back with their defaults
    # (e.g. tax=10.5) and overwrite the stored values.
    new_item = item.model_dump(exclude_unset=True)
    # orginal item into pydantic so we can copy it

    org_item_pydantic = Item(**org_item)  # ** unpacks the dict into keyword args
    # update it
    # model_copy(update=...) returns a NEW model: the stored values,
    # overwritten only by the keys present in new_item.
    final_item = org_item_pydantic.model_copy(update=new_item)

    # Save JSON-compatible data (a dict), not the Pydantic object.
    items[item_id] = jsonable_encoder(final_item)
    return final_item
    # Mentor note: this is a *partial* update (PATCH-style logic) on a PUT
    # route. Classic PUT replaces the whole record; the Day 5 notes say the
    # exclude_unset technique "can also be used with PUT", so this is valid -
    # just know that @app.patch is the conventional method for partial updates.
