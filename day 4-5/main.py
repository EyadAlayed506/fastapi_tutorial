from typing import Any
from fastapi.encoders import jsonable_encoder

from fastapi import FastAPI,status,HTTPException,Request
from pydantic import BaseModel, EmailStr
from fastapi.responses import JSONResponse
app = FastAPI()


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

#the password will be shown in the ouput (bad)


#better way

class UserIn(UserOut):
    password:str


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


@app.post("/user/",status_code=status.HTTP_200_OK,tags=["user"],
          summary="create a user",description=
          """
        creating a post using these info (username,email,fullname)
"""
,response_description="The created user"
#Don't build new code around it; migrate to the newer endpoint when possible.
) 
#tag makes documentation better
#we can use response_model
async def create_user (user:UserIn)->UserOut:
    return user



items = {"foo": "The Foo Wrestlers"}


class new_exception(Exception):
    def __init__(self,id):
        self.id=id

@app.exception_handler(new_exception)
async  def new_exception_handler(request:Request,exc:new_exception):
    return JSONResponse(
        status_code=401,
        content=f"sorry but we can not find item_id {exc.id}"
    )






@app.get("/items/{item_id}",tags=["items"])
async def read_item(item_id: str):
    if item_id not in items:
        raise new_exception(item_id)
    return {"item": items[item_id]}




items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}


class Item(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    tax: float = 10.5
    tags: list[str] = []


@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item) -> Item:#we are taking itemid and update its values using item
    if   item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND   ,
            detail=f" {item_id} was not found in the system"
        )                                                
    #item_id is the one we want to change
    #item is the one with the updated values
    org_item=items[item_id] #type of org_item is dic
    #new item without default values and type convert dict becasue(model_copy=dict)

    new_item=item.model_dump(exclude_unset=True) 
    #orginal item into pydantic so we can copy it

    org_item_pydantic=Item(**org_item)
    # update it
    final_item=org_item_pydantic.model_copy(update=new_item)
    
    items[item_id]=jsonable_encoder(final_item)
    return final_item



