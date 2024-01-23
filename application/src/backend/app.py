import os
import sys
import json
import shutil
import logging
import binascii
import subprocess

# Import utilities
from fsdicts import *
from runtypes import typechecker, Text, Optional
from guardify import *

# Import internal router
from router import router

from types import PasswordType, DeploymentType
from globals import DATABASE, AUTHORITY
from composer import Deployment

# Setup the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Read the temporary token validity
ACCESS_TOKEN_VALIDITY = int(os.environ.get("ACCESS_TOKEN_VALIDITY", str(60 * 10)))
PERMANENT_TOKEN_VALIDITY = int(os.environ.get("PERMANENT_TOKEN_VALIDITY", str(10 * 60 * 60 * 24 * 365)))


@typechecker
def PasswordType(password):
    # Convert the password to text
    password = Text(password)
    
    # Compare password to preset variable
    if password != os.environ.get("PASSWORD"):
        raise ValueError("PasswordType is incorrect")
    
	# Return the password
    return password


@typechecker
def DeploymentType(identifier):
    # Convert the identifier to text
    identifier = Text(identifier)

    # Create the deployment object
    deployment = Deployment(identifier)

    # Make sure identifier exists in database
    if not deployment.exists:
        raise ValueError("Deployment %r does not exist" % identifier)
    
    # Return the converted identifier
    return deployment

@router.post("/api/list", type_password=PasswordType)
def list(password):
    # Create a dictionary with ID->Name of deployments
    return {identifier: deployment.name for identifier, deployment in DATABASE.items()}


@router.post("/api/new", type_password=PasswordType)
def new(password):
    # Create new deployment identifier
    identifier = binascii.b2a_hex(os.urandom(4)).decode()

    # Create the new deployment
    deployment = Deployment(identifier)
    deployment.initialize()

    # Return the new ID
    return identifier


@router.post("/api/info", type_token=Token)
def info(token):
    """
    Fetches extended information about a deployment
    """

    # Parse token object and get ID
    identifier = DeploymentType(token.contents["id"])

    # Load the deployment
    return DATABASE[identifier]


@router.post("/api/pubkey", type_password=PasswordType, type_deployment=DeploymentType)
def pubkey(password, deployment):
    # Read the SSH key
    return deployment.pubkey


@router.post("/api/access", type_password=PasswordType, type_deployment=DeploymentType)
def access(password, deployment):
    # Create temporary access token
    token, _ = AUTHORITY.issue("Temporary access token for %s" % deployment.id, dict(id=deployment.id), [""], ACCESS_TOKEN_VALIDITY)

    # Return the created token
    return token


@router.post("/api/token", type_password=PasswordType, type_deployment=DeploymentType)
def token(password, deployment):
    """
    Generates two permanent access tokens
    1. General access token (log, update, restart, etc.)
    2. Webhook access token (Async restart)
    """

    # Issue token with general permissions
    general, _ = AUTHORITY.issue(str(), dict(id=deployment.id), [
        "log",
        "pull",
        "stop",
        "start",
        "status",
        "update",
        "restart",
    ], PERMANENT_TOKEN_VALIDITY)

    # Issue token with webhook permission
    webhook, _ = AUTHORITY.issue(str(), dict(id=deployment.id), ["webhook"], PERMANENT_TOKEN_VALIDITY)

    # Return the created tokens
    return dict(general=general, webhook=webhook)


@router.post("/api/edit", type_password=PasswordType, type_deployment=DeploymentType, type_name=Optional[Text], type_directory=Optional[Text], type_repository=Optional[Text])
def edit(password, deployment, name=None, directory=None, repository=None):
    # Edit the deployment
    return deployment.edit(name=name, directory=directory, repository=repository)


@router.post("/api/delete", type_password=PasswordType, type_deployment=DeploymentType)
def delete(password, deployment):
    return deployment.delete()


@router.post("/api/start", type_token=AUTHORITY.TokenType["start"])
def start(token):
    # Create deployment from token
    deployment = Deployment(token.contents["id"])

    # Start the deployment
    return deployment.start()

@router.post("/api/stop", type_token=AUTHORITY.TokenType["stop"])
def start(token, timeout=3):
    # Create deployment from token
    deployment = Deployment(token.contents["id"])

    # Start the deployment
    return deployment.stop(timeout)

@router.post("/api/start", type_token=AUTHORITY.TokenType["start"])
def start(token):
    # Create deployment from token
    deployment = Deployment(token.contents["id"])

    # Start the deployment
    return deployment.start()

