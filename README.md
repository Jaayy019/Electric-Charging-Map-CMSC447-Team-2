## Backend:
### How to run:
Git clone the repository
Create a virtual environment using your environment of choosing (`source venv/Scripts/activate`)

Run `pip install -r requirements.txt`

For contributing, also run:
`pip install -r requirements.txt -r requirements-dev.txt`

Copy `.env.example` to `.env` in the project root and set `OCM_API_KEY` to your Open Charge Map key. The `.env` file is ignored by Git and must not be committed.

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
From the project root (with your virtual environment activated):

```bash
python -m pytest tests/ -v
```

Shorter output: `pytest tests/ -v --tb=short` or timing: `pytest tests/ -q --durations=10`

On Windows PowerShell, activate the venv first, for example: `.\venv\Scripts\Activate.ps1`


3/4/2026 - 1:43 PM - "Basic React Map and Leaflet integration"
I added the leaflet map and used the React Map, it does work but the marker icon is broken.

3/9/2026 - 12:16 PM - "Custom icon implemented"
Added a new custom icon that can be used for all future charging stations.
