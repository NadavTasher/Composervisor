import os
import json
import logging
import binascii
import collections

from router import router

from constants import *
from database import Database

from puppy.process import execute
from puppy.thread.future import future
from puppy.typing.check import validate, kwargcheck
from puppy.typing.types import Text, Union, Optional
from puppy.token.authority import Authority

Data = Database("/opt/database.json")
Token = Authority(os.environ.get("SECRET").encode())
Deployment = collections.namedtuple("Deployment", ["id", "path", "name", "directory", "repository"])

ACTIONS = {
    # Management actions
    "pull": PULL_COMMAND,
    "update": UPDATE_COMMAND,
    "destroy": DESTROY_COMMAND,
    # State actions
    "stop": STOP_COMMAND,
    "start": START_COMMAND,
    "reset": RESET_COMMAND,
    "restart": RESTART_COMMAND,
    # Status actions
    "log": LOG_COMMAND,
    "status": STATUS_COMMAND
}


def TokenType(token):
    validate(password, Text)

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
    stdout, _ = execute("( %s ) 2>&1" % command.format(**parameters), check=check)

    # Return the output
    return stdout

@router.post("list")
@kwargcheck(password=PasswordType)
def _list(request, password=None):
    return Data.read()


@router.post("new")
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
    ~evaluate(MKDIR_COMMAND, deployment)
    ~evaluate(KEY_COMMAND, deployment)

    # Return the new ID
    return identifier


@router.post("fetch")
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


@router.post("token")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _token(request, password=None, identifier=None):
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
    return token


@router.post("update")
@kwargcheck(password=PasswordType, identifier=DeploymentType, name=str, directory=str, repository=str)
def _update(request, password=None, identifier=None, name=None, directory=None, repository=None):
    # Read database and update deployment
    database = Data.read()
    database[identifier] = dict(name=name, directory=directory, repository=repository)

    # Write the database
    Data.write(database)


@router.post("delete")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _delete(request, password=None, identifier=None):
    # Load deployment from database
    deployment = load(identifier)

    # Check if repository was cloned
    if os.path.exists(os.path.join(OUTPUT, identifier, REPOSITORY)):
        # Destroy the deployment
        ~evaluate(DESTROY_COMMAND, deployment, check=False)

    # Delete the directory
    ~evaluate(RMDIR_COMMAND, deployment, check=False)

    # Remove from the database
    database = Data.read()
    database.pop(identifier)
    Data.write(database)


@router.post("clone")
@kwargcheck(token=TokenType)
def _clone(request, token=None):
    # Parse token object and get ID
    token = Token.validate(token, name)

    # Load the deployment
    deployment = load(token.contents["id"])

    # Make sure the deployment was set-up
    assert deployment.repository, "Deployment repository was not set"
    assert deployment.directory, "Deployment directory was not set"

    # Check if repository is set-up
    assert not os.path.exists(os.path.join(deployment.path, REPOSITORY)), "Deployment repository is already set-up"

    # Format command and execute it
    return ~evaluate(CLONE_COMMAND, deployment)


@router.post("webhook")
@kwargcheck(token=TokenType)
def _webhook(request, token=None):
    # Parse token object and get ID
    token = Token.validate(token, name)

    # Load the deployment
    deployment = load(token.contents["id"])

    # Make sure the deployment was set-up
    assert deployment.repository, "Deployment repository was not set"
    assert deployment.directory, "Deployment directory was not set"

    # Check if repository is set-up
    assert not os.path.exists(os.path.join(deployment.path, REPOSITORY)), "Deployment repository is already set-up"

    # Format command and execute it
    evaluate(WEBHOOK_COMMAND, deployment)


# Create generic command execution actions
for name, command in ACTIONS.items():
    @router.post(name)
    @kwargcheck(token=TokenType)
    def _action(request, token=None):
        # Parse token object and get ID
        token = Token.validate(token, name)

        # Load the deployment
        deployment = load(token.contents["id"])

        # Make sure the deployment was set-up
        assert deployment.repository, "Deployment repository was not set"
        assert deployment.directory, "Deployment directory was not set"

        # Check if repository is set-up
        assert os.path.exists(os.path.join(deployment.path, REPOSITORY)), "Deployment repository is not initialized"

        # Format command and execute it
        return ~evaluate(command, deployment)
# yapf -ir . --style "{based_on_style: google, column_limit: 400, indent_width: 4}"
