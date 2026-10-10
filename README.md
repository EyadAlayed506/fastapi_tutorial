# FastAPI Learning Journey

My day-by-day notes and practice code from learning [FastAPI](https://fastapi.tiangolo.com/).
Each day folder holds the code I wrote, a copy of that code with educational comments,
and a PDF that teaches the day's concepts for revision.

**Start here:** [`fastapi_learning_overview.pdf`](fastapi_learning_overview.pdf) explains
what every day covers, its key code, and how the days build on each other.

## Contents

- [How each day is organized](#how-each-day-is-organized)
- [Learning roadmap](#learning-roadmap)
- [Setup with UV](#setup-with-uv)
- [Environment variables](#environment-variables)
- [Running the apps](#running-the-apps)
- [Database setup (day 10)](#database-setup-day-10)
- [Running the tests (day 8)](#running-the-tests-day-8)
- [Project structure](#project-structure)

## How each day is organized

| File | What it is |
| --- | --- |
| `main.py` | **Original code** - what I wrote while learning |
| `main_commented.py` | The same code with **educational comments** (same behavior, runnable) |
| `dayN_notes.pdf` | **Study notes**: objectives, explanations, examples from my code, common mistakes, revision summary |

Day 8 also has `test_main.py` (original tests) and `test_main_commented.py`.
Day 6 also has `day6_screen_recording.zip`, a recorded teaching session.

There is no `day1` or `day9` folder: only the days that have material in this repository are listed.

## Learning roadmap

| Day | Folder | Topics |
| --- | --- | --- |
| 2 | [`day2/`](day2/) | Path parameters and numeric validations (`Path`, `gt`/`le`), query parameters and string validations (`Query`, `min_length`/`max_length`), `Annotated`, reading 422 errors |
| 3 | [`day3/`](day3/) | Pydantic models for query parameters (`Annotated[Model, Query()]`), `Field`, `Literal`, `extra="forbid"`, nested body models, `HttpUrl`, `set` vs `list` |
| 4-5 | [`day4-5/`](day4-5/) | **Day 4:** response models and filtering a password out, status codes, path operation configuration (`tags`, `summary`, ...). **Day 5:** `HTTPException`, custom exception handlers, body updates (PUT vs PATCH, `exclude_unset` + `model_copy`) |
| 6 | [`day6/`](day6/) | Dependency injection with `Depends`, reusable `Annotated` aliases, sub-dependencies, classes as dependencies |
| 7 | [`day7/`](day7/) | Dependencies with `yield` (setup/teardown), `try/finally`, dependency chains and their execution order |
| 8 | [`day8/`](day8/) | Testing with `TestClient` and pytest: status codes, JSON bodies, validation errors |
| 10 | [`day10/`](day10/) | SQL databases with SQLModel + PostgreSQL: engine and session, table vs data models, CRUD, `exclude_unset` for PATCH, error types, credentials from `.env` |

## Setup with UV

This project uses [UV](https://docs.astral.sh/uv/) to manage Python and dependencies
(Python 3.13, see `.python-version`).

```bash
uv sync          # creates/updates .venv from pyproject.toml + uv.lock
```

Dependencies (in `pyproject.toml`): `fastapi[standard]`, `pydantic[email]`, `sqlmodel`,
`psycopg[binary]` (PostgreSQL driver), `python-dotenv`, and `pytest` as a dev dependency.
Add new packages with `uv add <package>` so `pyproject.toml` and `uv.lock` stay in sync.

## Environment variables

Only day 10 needs configuration (database credentials).

1. Copy the example file in the project root:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and put in your own PostgreSQL username and password.

`.env` is listed in `.gitignore`, so real credentials are never committed.
`.env.example` contains placeholders only.

| Variable | Required | Default |
| --- | --- | --- |
| `DB_USERNAME` | yes | - |
| `DB_PASSWORD` | yes | - |
| `DB_HOST` | no | `localhost` |
| `DB_PORT` | no | `5432` |
| `DB_NAME` | no | `heroes_db` |

If a required variable is missing, day 10 stops with a clear error message.

## Running the apps

Run any day from the project root with the FastAPI CLI (installed by `fastapi[standard]`):

```bash
uv run fastapi dev day2/main.py              # original code
uv run fastapi dev day2/main_commented.py    # commented copy, same behavior
```

Then open <http://127.0.0.1:8000/docs> to try the endpoints.
Replace `day2` with `day3`, `day4-5`, `day6`, `day7`, `day8` or `day10`.

For day 7, watch the terminal: each request to `/test/` prints the order in which the
dependencies open and close.

## Database setup (day 10)

Day 10 connects to **PostgreSQL** on `localhost:5432`, database `heroes_db`, using the
psycopg 3 driver.

1. Install and start PostgreSQL.
2. Create the database once, e.g. `createdb heroes_db` or in `psql`: `CREATE DATABASE heroes_db;`
3. Fill in `.env` (see above).
4. Run `uv run fastapi dev day10/main.py`. The `hero` table is created automatically on startup.

## Running the tests (day 8)

```bash
uv run pytest day8 -v
```

## Project structure

```
fastapi_tutorial/
|-- README.md
|-- pyproject.toml          # project + dependencies (UV)
|-- uv.lock                 # exact locked versions
|-- .python-version         # Python 3.13
|-- .gitignore
|-- .env.example            # placeholder credentials (copy to .env)
|-- fastapi_learning_overview.pdf   # one-document guide to every day
|-- src/fastapi_tutorial/   # package stub created by `uv init` (needed for the build)
|-- day2/     main.py, main_commented.py, day2_notes.pdf
|-- day3/     main.py, main_commented.py, day3_notes.pdf
|-- day4-5/   main.py, main_commented.py, day4-5_notes.pdf
|-- day6/     main.py, main_commented.py, day6_notes.pdf, day6_screen_recording.zip
|-- day7/     main.py, main_commented.py, day7_notes.pdf
|-- day8/     main.py, main_commented.py, test_main.py, test_main_commented.py, day8_notes.pdf
|-- day10/    main.py, main_commented.py, day10_notes.pdf
```
