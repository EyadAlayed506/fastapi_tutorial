# =============================================================================
# Day 8 - Testing: the app under test  (commented copy of main.py)
#
# Run the tests from the project root:
#     uv run pytest day8
# =============================================================================

from fastapi import FastAPI, HTTPException, Path
# Mentor note: TestClient, asyncio and HTTPException are imported but not used
# in this file. TestClient belongs in the TEST file (test_main.py), which is
# where it is actually used. Unused imports are harmless but can be removed.
from fastapi.testclient import TestClient
import asyncio
from typing import Annotated
app = FastAPI()


@app.get("/items/")
async def get_item():

    # Note: "massage" is a typo for "message". The tests don't check this
    # endpoint, so the typo goes unnoticed - a good reason to test every route.
    return {
        "massage": "all items"}


@app.get("/items/{item_id}")
# This function has the same Python name as the one above. Each route was
# already registered by its decorator, so both endpoints still work, but
# distinct names (e.g. get_all_items / get_item) avoid confusion.
async def get_item(item_id: Annotated[int,
                   # ge=1 -> item_id must be >= 1, so /items/0 returns 422.
                   # This is exactly what test_main.py checks.
                   Path(ge=1)],
                   # Plain default value -> optional query parameter.
                   q: str | None = None):

    return {
        "item_id": item_id,
        "q": q}
