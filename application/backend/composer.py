import os
import json
import logging
import binascii
import collections

from router import router

from constants import *
from database import Database

from puppy.process import execute
from puppy.typing.check import validate, kwargcheck
from puppy.typing.types import Text, Union, Optional
from puppy.token.authority import Authority

Data = Database("/opt/database.json")
Token = Authority(os.environ.get("SECRET").encode())
Deployment = collections.namedtuple("Deployment", ["id", "path", "name", "directory", "repository"])

def PasswordType(password):
    validate(password, Text)

    # Make sure password is valid
    assert password == os.environ.get("PASSWORD"), "Password is invalid!"

def DeploymentType(identifier):
    validate(identifier, Text)

    # Make sure ID exists in database
    database = Data.read()
    assert identifier in database.keys(), "Invalid deployment ID"

def load(identifier):
    # Read the database
    database = Data.read(identifier)

    # Read the deployment
    return Deployment(id=identifier, path=os.path.join(OUTPUT, identifier), **database[identifier])

def format(template, deployment):
    # Create deployment dict with escaped parameters
    parameters = {
        # Escape using JSON module
        name: json.dumps(value)[1:-1]
        # Loop over key-value in dict of deployment
        for name, value in deployment._asdict().items()
    }

    # Format with parameters
    return template.format(**parameters)

@router.post("/list")
@kwargcheck(password=PasswordType)
def _list(request, password=None):
    return Data.read()

@router.post("/new")
@kwargcheck(password=PasswordType)
def _new(request, password=None):
    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Update database with new deployment
    database = Data.read()
    database[identifier] = dict(name=None, directory=None, repository=None)
    Data.write(database)

    # Fetch the deployment object
    deployment = load(identifier)

    # Create directory and SSH access key
    execute(format(MKDIR_COMMAND, deployment))
    execute(format(KEY_COMMAND, deployment))

    # Return the new ID
    return identifier

@router.post("/fetch")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _fetch(request, password=None, identifier=None):
    # Read deployment SSH key
    with open(os.path.join(OUTPUT, identifier, PUBLIC), "rb") as key_file:
        key = key_file.read()

    # Create temporary access token
    token, _ = Token.issue("Temporary access token for %s" % identifier, dict(id=identifier), ["update"], 60 * 10)

    # Fetch general information about deployment
    deployment = load(identifier)
    
    # Return all information
    return dict(key=key.decode(), token=token.decode(), **deployment._asdict())

@router.post("/token")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _token(request, password=None, identifier=None):
    # Issue token with limited permissions
    token, _ = Token.issue(
        "Permenant access token for %s" % identifier, dict(id=identifier), [
						"pull",
						"stop",
						"start",
						"update",
						"restart",
						"webhook",
					], 
                    10 * 60 * 60 * 24 * 365)

    # Return the created token
    return token

@router.post("/update")
@kwargcheck(password=PasswordType, identifier=DeploymentType, name=str, directory=str, repository=str)
def _update(request, password=None, identifier=None, name=None, directory=None, repository=None):
    # Read database and update deployment
    database = Data.read()
    database[identifier] = dict(name=name, directory=directory, repository=repository)

    # Write the database
    Data.write(database)

@router.post("/delete")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _delete(request, password=None, identifier=None):
    # Load deployment from database
    deployment = load(identifier)

    # Check if repository was cloned
    if os.path.exists(os.path.join(OUTPUT, identifier, REPOSITORY)):
        # Destroy the deployment
        execute(format(DESTROY_COMMAND, deployment), check=False)

    # Delete the directory
    execute(format(RMDIR_COMMAND, deployment), check=False)

    # Remove from the database
    database = Data.read()
    database.pop(identifier)
    Data.write(database)