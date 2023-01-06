import os
import sys
import json
import bunch
import logging
import binascii

from router import router

from database import *
from constants import *

from puppy.process import execute
from puppy.filesystem import remove
from puppy.token.authority import Authority
from puppy.typing.check import validate, kwargcheck
from puppy.typing.types import Text, Union, Optional
from puppy.thread.future import future

# Initialize database and token generator
Data = Database("/opt/database.json")
Token = Authority(os.environ.get("SECRET").encode())


def TokenType(token):
    validate(token, Text)
    Token.validate(token)


def PasswordType(password):
    validate(password, Text)
    assert password == os.environ.get("PASSWORD"), "Password is invalid!"


def DeploymentType(identifier):
    validate(identifier, Text)
    assert identifier in Data.read().keys(), "Invalid deployment ID"


@future
def evaluate(command, identifier=None, **parameters):
    """
    Formats a command with the given parameters (and changed working directory)
    """

    # Escape parameters for execution
    escaped_parameters = {
        # Escape using JSON module
        name: json.dumps(value)[1:-1]
        # Loop over key-value in dict of deployment
        for name, value in parameters.items()
    }

    # Render command with parameters
    rendered_command = command.format(identifier=identifier, **escaped_parameters)

    # Change CWD of execution
    cwd_command = f"cd {OUTPUT} && cd {identifier} && %s" % rendered_command

    # Execute command and return output
    return execute(cwd_command)


def register(action, command, setup, asyncronous):
    """
    Registers a deployment action
    An action is a command that gets formatted with parameters
    """

    @router.post(action)
    @kwargcheck(token=TokenType)
    def _action(request, token, **ignored):
        # Parse token object and get ID
        identifier = bunch.Bunch(Token.validate(token, action).contents).id

        # Load the deployment
        deployment = Data.get(identifier)

        # Make sure the deployment was set-up
        assert deployment.repository, "Deployment repository was not set"
        assert deployment.directory, "Deployment directory was not set"

        # Make sure setup requirements are met
        assert os.path.exists(os.path.join(OUTPUT, identifier, REPOSITORY)) == setup, "Deployment repository setup requirements not met"

        # Format command and execute it
        execution = evaluate(command, identifier, **deployment)

        # Check if should skip result
        if not asyncronous:
            return (~execution).decode()


@router.post("list")
@kwargcheck(password=PasswordType)
def _list(request, password):
    """
    Lists all deployment with configuration values
    """

    return Data.read()


@router.post("info")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _info(request, password, identifier):
    """
    Fetches extended information about a deployment
    """

    # Read deployment SSH key
    with open(os.path.join(OUTPUT, identifier, PUBLIC), "rb") as key_file:
        key = key_file.read()

    # Create temporary access token
    token, _ = Token.issue("Temporary access token for %s" % identifier, dict(id=identifier), list(ACTIONS.keys()), 60 * 10)

    # Return all information
    return dict(key=key.decode(), token=token.decode(), **Data.get(identifier))


@router.post("token")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _token(request, password, identifier):
    """
    Generates two permenant access tokens
    1. General access token (log, update, restart, etc.)
    2. Webhook access token (Async restart)
    """

    # Issue token with general permissions
    general, _ = Token.issue("General token", dict(id=identifier), [
        "log",
        "pull",
        "stop",
        "start",
        "update",
        "restart",
    ], 10 * 60 * 60 * 24 * 365)

    # Issue token with webhook permission
    webhook, _ = Token.issue(str(), dict(id=identifier), ["webhook"], 10 * 60 * 60 * 24 * 365)

    # Return the created tokens
    return (general.decode(), webhook.decode())


@router.post("new")
@kwargcheck(password=PasswordType)
def _new(request, password):
    """
    Creates a new deployment
    """

    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Update database with new deployment
    Data.set(identifier, dict(name=None, directory=None, repository=None))

    # Create directory for deployment
    os.makedirs(os.path.join(OUTPUT, identifier))

    # Create SSH access key for deployment
    ~evaluate(KEY_COMMAND, identifier)

    # Return the new ID
    return identifier


@router.post("edit")
@kwargcheck(password=PasswordType, identifier=DeploymentType, deployment=dict(name=Text, directory=Text, repository=Text))
def _edit(request, password, identifier, deployment):
    """
    Edits an existing deployment
    """

    Data.set(identifier, deployment)


@router.post("delete")
@kwargcheck(password=PasswordType, identifier=DeploymentType)
def _delete(request, password, identifier):
    """
    Deletes an existing deployment
    """

    # Check if repository was cloned
    if os.path.exists(os.path.join(OUTPUT, identifier, REPOSITORY)):
        # Destroy the deployment
        try:
            ~evaluate(DESTROY_COMMAND, identifier, **Data.get(identifier))
        except:
            pass

    # Delete the directory
    remove(os.path.join(OUTPUT, identifier))

    # Remove from the database
    Data.remove(identifier)


for name, (command, setup, asyncronous) in ACTIONS.items():
    register(name, command, setup, asyncronous)
