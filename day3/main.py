from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field,HttpUrl

app = FastAPI()


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100,description="limite must be between 0-100")#u can use query(...) isntead
    offset: int = Field(0, ge=0,title="offset")
    order_by: Literal["created_at", "updated_at"] = "created_at"
     #either of them default created_at
    tags: list[str] = []


@app.get("/items/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    #take the values from query
    
    return filter_query





class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
    image: Image | None = None


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    results = {"item_id": item_id, "item": item}
    return results