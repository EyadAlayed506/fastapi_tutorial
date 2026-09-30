from fastapi import FastAPI,HTTPException,Path
from fastapi.testclient import TestClient
import asyncio
from typing import Annotated
app = FastAPI()



@app.get("/items/")
async def get_item():
  
    return {
    "massage": "all items"}






@app.get("/items/{item_id}")
async def get_item(item_id:Annotated[int,
                   Path(ge=1)],
                   q:str|None=None):
 
   
    return {
    "item_id":item_id,
    "q": q}



