import os
import json
import logging
import binascii

from router import router

from constants import *
from database import Database

from puppy.process import execute
from puppy.typing.check import kwargcheck
from puppy.typing.types import Literal, Optional
from puppy.token.autority import Authority

DATABASE = Database("/opt/database.json")
PASSWORD = Literal[os.environ.get("PASSWORD")]
AUTHORITY = Authority(os.environ.get("SECRET"))

def validate_deployment(function):
    @kwargcheck(token=str)
    def wrapper(request, **kwargs):
        pass
    return function

def fetch_deployment(identifier):
    pass

@router.post("/list")
@kwargcheck(password=PASSWORD)
def list_deployments(request, **kwargs):
    return DATABASE.read()

@router.post("/new")
@kwargcheck(password=PASSWORD)
def new_deployment(request, **kwargs):
    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Read database for updating
    database = DATABASE.read()
    
    # Update database with new deployment
    database[identifier] = {"name": None, "directory": None, "repository": None}

    # Write database with updated data
    DATABASE.write(database)

    # Fetch the deployment object
    deployment = fetch_deployment(identifier)

    # Create directory and SSH access key
    execute(MKDIR_COMMAND.format(**deployment))
    execute(KEY_COMMAND.format(**deployment))