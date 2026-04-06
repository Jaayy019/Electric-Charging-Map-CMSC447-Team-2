## Backend:
### How to run:
Git clone the repository
Create a virtual environment using your environment of choosing (`source venv/Scripts/activate`)

Run `pip install -r requirements.txt`

For contributing, also run:
`pip install -r requirements.txt -r requirements-dev.txt`

Copy `.env.example` to `.env` in the project root and set `OCM_API_KEY` to your Open Charge Map key. The `.env` file is ignored by Git and must not be committed.

For Neon: set **`DATABASE_DEV_URL`** to your dev branch connection string (and optionally **`DATABASE_URL`** for prod). If **`DATABASE_DEV_URL`** is set, the backend uses it first. After tables exist, you can load sample rows into Postgres with:

`python scripts/seed_dev_db.py`

(from the repo root, with the venv activated). The script skips if `charge_points` already has data.

To run the backend go run the python file api/main.py
To open up the docs to test the API go to `http://localhost:5000/docs`
The docs will describe to you how to request charging port data from the back end


### Backend Limitations
The only API currently implemented is one to retrieve charging ports

How to start the frontend:

1. cd into the frontend folder
2. Do "npm install" to install node modules folder and dependencies
3. Use "npm start", app launches on http://localhost:3000

In the event of errors:

Outdated or conflicting packages:
1. "rm -rf node_modules"
2. "npm install"

If using powershell:
1. "rmdir node_modules -Recurse -Force"
2. "npm install"

Once done: "npm start"

### Tests
Backend tests live in `tests/` and use **pytest** with **pytest-asyncio** (API and database routes against an in-memory SQLite DB). Install dependencies from the repo root with your virtual environment activated:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the full suite (recommended — same entry point as CI):

```bash
python -m pytest tests/ -v
```

Run with coverage (needs `requirements-dev.txt` for `pytest-cov`, and matches the coverage gate in GitHub Actions):

```bash
python -m pytest tests/ -v --cov=api --cov=database --cov-report=term-missing
```

Helpful options: `pytest tests/ -q` (quieter), `pytest tests/ -v --tb=short` (shorter tracebacks), `pytest tests/ -q --durations=10` (slowest tests).

**Linting (optional, also runs in CI):** `ruff check .` and `ruff format --check .` from the project root.

**CI:** Pushes and pull requests to `main` run tests, Ruff, `pip-audit`, and a UTF-8 check on `requirements.txt` via GitHub Actions (`.github/workflows/ci.yml`).

**Windows:** Activate the venv first, e.g. PowerShell `.\venv\Scripts\Activate.ps1`, or Git Bash `source venv/Scripts/activate`.


3/4/2026 - 1:43 PM - "Basic React Map and Leaflet integration"
I added the leaflet map and used the React Map, it does work but the marker icon is broken.

3/9/2026 - 12:16 PM - "Custom icon implemented"
Added a new custom icon that can be used for all future charging stations.
