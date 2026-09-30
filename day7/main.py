from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()


# Dependency A
async def get_resource():
    print("A open")
    try:
        yield "conn -1"
    finally:
        print("A close")


# Dependency B depends on A
async def get_sub(
    resource: Annotated[str, Depends(get_resource)]
):
    print("B open")
    try:
        yield f"sub using {resource}"
    finally:
        print("B close")


# Path operation
@app.get("/test/")
def get_value(
    value: Annotated[str, Depends(get_sub)]
):
    print("endpoint")
    return value

#a open
#b open
#endpoint
# return sub using conn1
#b close
#a close