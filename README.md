## Backend:
### How to run:
Git clone the repository
Create a virtual environment using your environment of choosing
Run `pip install -r requirements.txt`

In the file called `.env` in the root of the repository, replace API_KEY with the correct API key in discord

To run the backend go run the python file api/main.py
To open up the docs to test the API go to `http://localhost:5000/docs`
The docs will describe to you how to request charging port data from the back end


### Backend Limitations
The only API currently implemented is one to retrieve charging ports
