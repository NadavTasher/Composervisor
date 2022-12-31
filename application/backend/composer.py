import os
import sys
import json
import logging
import binascii
import collections

from router import router

from constants import *
from database import Database

from puppy.process import execute
from puppy.filesystem import remove
from puppy.thread.future import future
from puppy.typing.check import validate, kwargcheck
from puppy.typing.types import Text, Union, Optional
from puppy.token.authority import Authority

Data = Database("/opt/database.json")
Token = Authority(os.environ.get("SECRET").encode())
Deployment = collections.namedtuple("Deployment", ["id", "path", "name", "directory", "repository"])

ACTIONS = {
    # Management actions
    "pull": (PULL_COMMAND, True, False),
    "clone": (CLONE_COMMAND, False, False),
    "update": (UPDATE_COMMAND, True, False),
    "destroy": (DESTROY_COMMAND, True, False),
    # State actions
    "stop": (STOP_COMMAND, True, False),
    "start": (START_COMMAND, True, False),
    "reset": (RESET_COMMAND, True, False),
    "restart": (RESTART_COMMAND, True, False),
    # Status actions
    "log": (LOG_COMMAND, True, False),
    "status": (STATUS_COMMAND, True, False),
    # Webhook action
    "webhook": (WEBHOOK_COMMAND, True, True)
}

def TokenType(token):
    validate(token, Text)

    # Validate the token
    Token.validate(token)


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


def register(action, command, setup, asyncronous):

    @router.post(action)
    @kwargcheck(token=TokenType)
    def _action(request, token):
        # Parse token object and get ID
        token = Token.validate(token, action)

        # Load the deployment
        deployment = load(token.contents["id"])

        # Make sure the deployment was set-up
        assert deployment.repository, "Deployment repository was not set"
        assert deployment.directory, "Deployment directory was not set"

        # Check if repository is set-up
        exists = os.path.exists(os.path.join(OUTPUT, deployment.id, REPOSITORY))

        # Make sure setup requirements are met
        assert setup == exists, "Deployment repository setup requirements not met"

        # Format command and execute it
        execution = evaluate(command, deployment)

        # Check if should skip result
        if not asyncronous:
            return (~execution).decode()


@future
def evaluate(command, deployment, check=True):
    # Create deployment dict with escaped parameters
    parameters = {
        # Escape using JSON module
        name: json.dumps(value)[1:-1]
        # Loop over key-value in dict of deployment
        for name, value in deployment._asdict().items()
    }

    # Execute command and return output
    return execute(f"cd {OUTPUT}; cd {deployment.id}; %s" % command.format(**parameters), check=check)


@router.post("list")
@kwargcheck(password=PasswordType)
def _list(request, password):
    return Data.read()


@router.post("info")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _info(request, password, identifier):
    # Read deployment SSH key
    with open(os.path.join(OUTPUT, identifier, PUBLIC), "rb") as key_file:
        key = key_file.read()

    # Create temporary access token
    token, _ = Token.issue("Temporary access token for %s" % identifier, dict(id=identifier), list(ACTIONS.keys()), 60 * 10)

    # Fetch general information about deployment
    deployment = load(identifier)

    # Return all information
    return dict(key=key.decode(), token=token.decode(), **deployment._asdict())


@router.post("token")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _token(request, password, identifier):
    # Issue token with limited permissions
    token, _ = Token.issue("Permenant access token for %s" % identifier, dict(id=identifier), [
        "pull",
        "stop",
        "start",
        "update",
        "restart",
        "webhook",
    ], 10 * 60 * 60 * 24 * 365)

    # Return the created token
    return token.decode()


@router.post("new")
@kwargcheck(password=PasswordType)
def _new(request, password):
    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Update database with new deployment
    database = Data.read()
    database[identifier] = dict(name=None, directory=None, repository=None)
    Data.write(database)

    # Fetch the deployment object
    deployment = load(identifier)

    # Create directory for deployment
    os.makedirs(os.path.join(OUTPUT, identifier))
    
    # Create SSH access key for deployment
    ~evaluate(KEY_COMMAND, deployment)

    # Return the new ID
    return identifier


@router.post("edit")
@kwargcheck(password=PasswordType, identifier=DeploymentType, name=Text, directory=Text, repository=Text)
def _edit(request, password, identifier, name, directory, repository):
    # Read database and update deployment
    database = Data.read()
    database[identifier] = dict(name=name, directory=directory, repository=repository)

    # Write the database
    Data.write(database)


@router.post("delete")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _delete(request, password, identifier):
    # Load deployment from database
    deployment = load(identifier)

    # Check if repository was cloned
    if os.path.exists(os.path.join(deployment.path, REPOSITORY)):
        # Destroy the deployment
        ~evaluate(DESTROY_COMMAND, deployment, check=False)

    # Delete the directory
    remove(os.path.join(OUTPUT, identifier))

    # Remove from the database
    database = Data.read()
    database.pop(identifier)
    Data.write(database)


for name, (command, setup, asyncronous) in ACTIONS.items():
    register(name, command, setup, asyncronous)
