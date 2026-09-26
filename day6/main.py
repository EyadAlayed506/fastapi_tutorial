from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


CommonsDep = Annotated[dict, Depends(common_parameters)] #call function common_parameter anad pass it to commnsDep
#that prevent redudent code


@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons


@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons


# we can do it with classes (more optimal than functions in this case)

class common_parameters_class:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

item_filtered=Annotated[common_parameters_class,Depends(common_parameters_class)]
@app.get("/items_class/")
async def read_items(commons:item_filtered):
    response={}
    if commons.q:
        response.update({"q":commons.q})

    items=fake_items_db[commons.skip:commons.skip+commons.limit]
    response.update({"items":items})
    return response


