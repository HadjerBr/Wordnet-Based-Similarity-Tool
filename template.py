import os
from pathlib import Path
import logging


logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s')

list_of_files = [
    "db_importer.py",
    "app.py",
    "requirements.txt",
    "research/trials.ipynb", 
    "templates/index.html",
    "db_importer.py",
    "similarity.py",
    
    
]


for filepath in list_of_files:
    filepath = Path(filepath) # convert to the OS path
    filedir, filename = os.path.split(filepath) # gives the files name and the folder name

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file: {filename}") # creating the folder

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0): # if the file does not exist, create an empty file
        with open(filepath, "w") as f:
            pass
        logging.info(f"Creating empty file: {filepath}")

    else:
        logging.info(f"{filename} already exists") # if the file already exists print this