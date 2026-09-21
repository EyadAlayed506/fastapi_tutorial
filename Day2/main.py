from fastapi import FastAPI, Path, Query
from typing import Annotated
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


@app.get("/items/{item_id}")
async def get_item_id(item_id:Annotated[int,Path(gt=0,le=1000)]
                      ,q: Annotated[str | None, Query(min_length=3, max_length=50)]= None ):
    return {"id":item_id,
            "q":q}