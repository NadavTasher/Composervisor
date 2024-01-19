import os
import sys
import json
import shutil
import logging
import binascii
import subprocess

# Import utilities
from fsdicts import *
from runtypes import *
from guardify import *

# Import internal router
from router import router

# Create some constants
DEPLOYMENTS_DIRECTORY = "/opt/deployments"
PRIVATE_KEY_NAME = "id_rsa"
PUBLIC_KEY_NAME = PRIVATE_KEY_NAME + ".pub"

# Setup the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# Initialize database and token generator
database = fastdict("/opt/database")
authority = Authority(os.environ["SECRET"].encode())


@typechecker
def Item(item):
    return Schema[dict(name=Text, directory=Text, repository=Text)](item)


@typechecker
def Password(password):
    # Make sure token is a text
    if not isinstance(password, Text):
        return False

    # Compare password to preset variable
    return password == os.environ.get("PASSWORD")


@typechecker
def Identifier(identifier):
    # Convert the identifier to text
    identifier = Text(identifier)

    # Make sure identifier exists in database
    if identifier not in database:
        raise Exception("%r is not a deployment" % identifier)
    
    # Return the converted identifier
    return identifier


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

    # Add working directory to command
    command = f"cd {DEPLOYMENT} && %s" % command

    # Render command with parameters
    command = command.format(identifier=identifier, **escaped_parameters)

    # Execute command and return DEPLOYMENTS_DIRECTORY
    return execute(command)


def register(action, command, setup, asyncronous):
    """
    Registers a deployment action
    An action is a command that gets formatted with parameters
    """

    @router.post(action, type_token=authority.TokenType[action])
    def _action(token, **ignored):
        # Parse token object and get ID
        identifier = Identifier(token.contents["id"])

        # Load the deployment
        deployment = database[identifier]

        # Make sure the deployment was set-up
        assert deployment.repository, "Deployment repository was not set"
        assert deployment.directory, "Deployment directory was not set"

        # Make sure setup requirements are met
        assert os.path.exists(os.path.join(DEPLOYMENTS_DIRECTORY, identifier, REPOSITORY)) == setup, "Deployment repository setup requirements not met"

        # Format command and execute it
        execution = evaluate(command, identifier, **deployment)

        # Check if should skip result
        if not asyncronous:
            return (~execution).decode()


@router.post("list", type_password=Password)
def _list(password):
    """
    Lists all deployment with configuration values
    """

    # Create a dictionary with ID->Name of deployments
    return {identifier: deployment.name for identifier, deployment in database.items()}


@router.post("new", type_password=Password)
def _new(password):
    """
    Creates a new deployment
    """

    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Update database with new deployment
    database[identifier] = dict(name=None, directory=None, repository=None)

    # Create deployment path from identifier
    directory = os.path.join(DEPLOYMENTS_DIRECTORY, identifier)

    # Create directory for deployment
    os.makedirs(directory)

    # Create SSH access key for deployment
    subprocess.check_call(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", PRIVATE_KEY_NAME, "-N", str(), "Deployment key for %s" % identifier], cwd=directory)

    # Return the new ID
    return identifier


@router.post("info", type_token=authority.TokenType)
def _info(token):
    """
    Fetches extended information about a deployment
    """

    # Parse token object and get ID
    identifier = Identifier(token.contents["id"])

    # Load the deployment
    return database[identifier]


@router.post("key", type_password=Password, type_identifier=Identifier)
def _key(password, identifier):
    # Read deployment SSH key
    with open(os.path.join(DEPLOYMENTS_DIRECTORY, identifier, PUBLIC), "rb") as key_file:
        key = key_file.read()

    # Return decoded key
    return key.decode()


@router.post("access", type_password=Password, type_identifier=Identifier)
def _access(password, identifier):
    """
    Generate a temporary access token for a deployment
    """

    # Create temporary access token
    token, _ = authority.issue("Temporary access token for %s" % identifier, dict(id=identifier), list(ACTIONS.keys()), 60 * 10)

    # Return the created token
    return token.decode()


@router.post("token", type_password=Password, type_identifier=Identifier)
def _token(password, identifier):
    """
    Generates two permanent access tokens
    1. General access token (log, update, restart, etc.)
    2. Webhook access token (Async restart)
    """

    # Issue token with general permissions
    general, _ = authority.issue(str(), dict(id=identifier), [
        "log",
        "pull",
        "stop",
        "start",
        "status",
        "update",
        "restart",
    ], 10 * 60 * 60 * 24 * 365)

    # Issue token with webhook permission
    webhook, _ = authority.issue(str(), dict(id=identifier), ["webhook"], 10 * 60 * 60 * 24 * 365)

    # Return the created tokens
    return dict(general=general.decode(), webhook=webhook.decode())


@router.post("edit", type_password=Password, type_identifier=Identifier, type_deployment=Item)
def _edit(password, identifier, deployment):
    """
    Edits an existing deployment
    """

    database[identifier] = deployment


@router.post("delete", type_password=Password, type_identifier=Identifier)
def _delete(password, identifier):
    """
    Deletes an existing deployment
    """

    # Check if repository was cloned
    if os.path.exists(os.path.join(DEPLOYMENTS_DIRECTORY, identifier, REPOSITORY)):
        # Destroy the deployment
        try:
            ~evaluate(DESTROY_COMMAND, identifier, **database[identifier])
        except:
            pass

    # Delete the directory
    shutil.rmtree(os.path.join(DEPLOYMENTS_DIRECTORY, identifier))

    # Remove from the database
    del database[identifier]


for name, (command, setup, asyncronous) in ACTIONS.items():
    register(name, command, setup, asyncronous)
