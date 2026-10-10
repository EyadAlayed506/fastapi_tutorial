# =============================================================================
# Day 10 - SQL (relational) databases with SQLModel + PostgreSQL
#          (commented copy of main.py)
#
# Setup (once):
#   1. PostgreSQL running on localhost:5432 with a database called heroes_db
#   2. copy .env.example to .env in the project root and fill in
#      DB_USERNAME and DB_PASSWORD
# Run it from the project root:
#     uv run fastapi dev day10/main_commented.py
# =============================================================================

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

# SQLModel = Pydantic (validation/JSON) + SQLAlchemy (database) in one class.
#   Field         -> column options (primary_key, index, default)
#   Session       -> one "unit of work" with the database
#   SQLModel      -> base class; with table=True it becomes a real table
#   create_engine -> creates the object that manages database connections
#   select        -> builds a SELECT query in Python instead of raw SQL
from sqlmodel import Field, Session, SQLModel, create_engine, select


# -----------------------------------------------------------------------------
# Version 1 (kept commented out, as in main.py)
# -----------------------------------------------------------------------------
# class Hero(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True) #the default is none eventhoug it is key? because we want let sql do the id instead
#     # hero1=hero(name="eyad",age=21,secret_name="esa") this is allowed because sql will create the id
#     name: str = Field(index=True)
#     age: int | None = Field(default=None, index=True)
#     secret_name: str
#
# Why it MUST stay commented out: every class with table=True registers a
# table in SQLModel.metadata. Defining Hero twice in one file raises
# "Table 'hero' is already defined" on import and the app never starts.

# Code below omitted

import os
from dotenv import load_dotenv
from sqlalchemy import URL

# load_dotenv() finds the .env file (searching from this file's folder
# upwards, so the project-root .env is found) and copies its KEY=value lines
# into the process environment. os.getenv then reads them.
# Secrets live in .env (ignored by git), NOT in the source code.
load_dotenv()  # reads the .env file in the project root (it is ignored by git)

password = os.getenv("DB_PASSWORD")
username = os.getenv("DB_USERNAME")

# os.getenv returns None for a missing variable. Failing early with a clear
# message is much better than a confusing database login error later.
if not username or not password:
    raise RuntimeError(
        "DB_USERNAME and DB_PASSWORD must be set. "
        "Copy .env.example to .env in the project root and fill in your values."
    )

# URL.create keeps the credentials separate, so special characters
# in the password (like @ or :) don't break the connection string
#
# An f-string like f"postgresql+psycopg://{username}:{password}@localhost..."
# breaks if the password contains @, :, / or #, because those characters have
# a meaning inside a URL. URL.create escapes each part for us.
#   drivername "postgresql+psycopg" = database type + Python driver (psycopg 3)
database_url = URL.create(
    drivername="postgresql+psycopg",
    username=username,
    password=password,
    host=os.getenv("DB_HOST", "localhost"),       # second argument = default
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "heroes_db"),
)

# The ENGINE holds the connection pool. Create ONE per application; it lives
# as long as the app process. Tip: create_engine(database_url, echo=True)
# prints every SQL statement - great for learning.
engine = create_engine(database_url)


def create_db_and_tables():
    # Creates every table registered with table=True - but ONLY tables that do
    # not exist yet. It never adds/removes columns of an existing table
    # (that is what migration tools such as Alembic are for).
    SQLModel.metadata.create_all(engine)  # create all tables above {hero}


# Code above omitted 👆

# A dependency with yield (Day 7 pattern!). Each request gets its OWN session:
#   - `with` opens the session
#   - yield hands it to the endpoint
#   - after the response, the `with` block ends and the session is closed
def get_session():  # each request has it own session it holds the chagnes before commit them
    with Session(engine) as session:
        yield session


# Reusable alias (Day 6 pattern): any endpoint parameter typed SessionDep
# receives a fresh database session.
SessionDep = Annotated[Session, Depends(get_session)]

# Code below omitted 👇


# Code above omitted 👆

app = FastAPI()


# Runs once when the server starts: makes sure the tables exist.
# Note: @app.on_event is the older style (FastAPI shows a deprecation
# warning). The current style is a `lifespan` function - fine to learn later.
@app.on_event("startup")  # after the application starts it begin with this
def on_startup():
    create_db_and_tables()

# Code below omitted 👇


# Code above omitted 👆

# -----------------------------------------------------------------------------
# Version 1 endpoints (kept commented out, as in main.py)
# -----------------------------------------------------------------------------
# @app.post("/heroes/")
# def create_hero(hero: Hero, session: SessionDep) -> Hero:
#     session.add(hero) #add the changes
#     session.commit() #apply them in sql
#     session.refresh(hero) # update python with the new value
#     return hero

# Code below omitted 👇


# Code above omitted 👆

# @app.get("/heroes/")
# def read_heroes(
#     session: SessionDep,
#     offset: int = 0,
#     limit: Annotated[int, Query(le=100)] = 100,
# ) -> list[Hero]:
#     heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
#     return heroes

# # Code below omitted 👇


# # Code above omitted 👆

# @app.get("/heroes/{hero_id}")
# def read_hero(hero_id: int, session: SessionDep) -> Hero:
#     hero = session.exec(select (Hero).where(Hero.id==hero_id))
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero
#
# BUG in this v1 read_hero: session.exec(...) returns a RESULT object (a "box"
# of rows), not a Hero. The box is truthy even when empty, so the 404 never
# fires, and returning the box gives a 500. Fix: add .first()
#     hero = session.exec(select(Hero).where(Hero.id == hero_id)).first()
# or simply use session.get(Hero, hero_id) as version 2 does.

# # Code below omitted 👇


# # Code above omitted 👆

# @app.delete("/heroes/{hero_id}")
# def delete_hero(hero_id: int, session: SessionDep):
#     hero = session.get(Hero, hero_id)  # we can retrive based on id different way as explaned above
#     if not hero: # if hero is not None
#         raise HTTPException(status_code=404, detail="Hero not found")
#     session.delete(hero)
#     session.commit()
#     return {"ok": True}
#
# (The comment "if hero is not None" above is backwards: `if not hero` means
#  "if hero IS None" - i.e. not found.)

# we have problems with the above code
# 1- client genrate the id not the database
# 2-secrete name is returned


# Code above omitted 👆

# -----------------------------------------------------------------------------
# Version 2: one model per job
# -----------------------------------------------------------------------------
# HeroBase    -> shared fields, NOT a table (no table=True)
# Hero        -> the real table (adds id + secret_name)
# HeroPublic  -> what we RETURN (id guaranteed, secret_name never included)
# HeroCreate  -> what the client SENDS to create (no id: the DB generates it)
# HeroUpdate  -> what the client SENDS to update (every field optional)
class HeroBase(SQLModel):
    # index=True -> the database builds an index so searching by name is fast
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    # id is None BEFORE saving; the database assigns it on INSERT.
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str


class HeroPublic(HeroBase):
    # After saving, id always exists -> `int` (not `int | None`) is a promise
    # to API clients that they never need to check for None.
    id: int


class HeroCreate(HeroBase):
    secret_name: str


class HeroUpdate(HeroBase):
    # Re-declared with default None so the client can send only what changes.
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None

# Code below omitted 👇

# Code above omitted 👆


# response_model=HeroPublic is used (instead of `-> HeroPublic`) because the
# function really returns a Hero table object; FastAPI converts/filters it
# into HeroPublic, so secret_name is dropped from the response.
@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)  # take the values from herocreate and apply it to hero class and let sql do the id
    session.add(db_hero)       # stage the new row in the session (not saved yet)
    session.commit()           # send INSERT to the database and save it
    session.refresh(db_hero)   # reload from the DB -> db_hero.id is now filled in
    return db_hero

# Code below omitted 👇


# Code above omitted 👆

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,                               # how many rows to skip
    limit: Annotated[int, Query(le=100)] = 100,    # at most 100 per page
):
    # select(Hero)              -> SELECT * FROM hero
    # .offset(...).limit(...)   -> pagination
    # session.exec(...)         -> runs it, returns a result "box"
    # .all()                    -> opens the box: list[Hero] ([] if none)
    # Tip: add .order_by(Hero.id) so pages come back in a guaranteed order.
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

# Code below omitted 👇


# Code above omitted 👆

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    # session.get(Model, primary_key) -> the object, or None if not found.
    hero = session.get(Hero, hero_id)
    if not hero:  # `if hero is None:` says the same thing more explicitly
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
# SQL retrieves the hero whose ID matches hero_id,
#  including all its fields. FastAPI then filters the response using HeroPublic,
# excluding any fields that aren't defined in that model.


@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_her(hero_id: int, session: SessionDep, hero: HeroUpdate):  # (name typo: update_hero)
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    # exclude_unset=True separates "the client didn't mention it" from
    # "the client sent null". Without it, unsent fields would be None and
    # secret_name=None would break the NOT NULL rule -> 500.
    hero_data = hero.model_dump(exclude_unset=True)  # exclude the fields that were not provided
    hero_db.sqlmodel_update(hero_data)   # copy only those fields onto the row
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db


@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)   # mark the row for deletion
    session.commit()       # DELETE is executed here
    return {"ok": True}
