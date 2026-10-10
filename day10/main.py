from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


# class Hero(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True) #the default is none eventhoug it is key? because we want let sql do the id instead
#     # hero1=hero(name="eyad",age=21,secret_name="esa") this is allowed because sql will create the id 
#     name: str = Field(index=True)
#     age: int | None = Field(default=None, index=True)
#     secret_name: str

# Code below omitted 

import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("DB_PASSWORD")
username = os.getenv("DB_USERNAME")

sqlite_url = (
    f"postgresql+psycopg://{username}:{password}"
    "@localhost:5432/heroes_db"
)

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine) #create all tables above {hero}



# Code above omitted 👆

def get_session(): # each request has it own session it holds the chagnes before commit them
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

# Code below omitted 👇


# Code above omitted 👆

app = FastAPI()


@app.on_event("startup") #after the application starts it begin with this
def on_startup():
    create_db_and_tables()

# Code below omitted 👇


# Code above omitted 👆

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

# we have problems with the above code
#1- client genrate the id not the database
#2-secrete name is returned


# Code above omitted 👆

class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)


class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str


class HeroPublic(HeroBase):
    id: int


class HeroCreate(HeroBase):
    secret_name: str


class HeroUpdate(HeroBase):
    name: str | None = None
    age: int | None = None
    secret_name: str | None = None

# Code below omitted 👇

# Code above omitted 👆

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero) # take the values from herocreate and apply it to hero class and let sql do the id
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

# Code below omitted 👇


# Code above omitted 👆

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

# Code below omitted 👇


# Code above omitted 👆

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
#SQL retrieves the hero whose ID matches hero_id,
#  including all its fields. FastAPI then filters the response using HeroPublic, 
# excluding any fields that aren't defined in that model.
@app.patch("/heroes/{hero_id}",response_model=HeroPublic)
def update_her(hero_id:int,session:SessionDep,hero:HeroUpdate):
    hero_db=session.get(Hero,hero_id)
    if not hero_db:
        raise HTTPException(status_code=404,detail="Hero not found")
    hero_data=hero.model_dump(exclude_unset=True) #exclude the fields that were not provided
    hero_db.sqlmodel_update(hero_data)
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db



@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}