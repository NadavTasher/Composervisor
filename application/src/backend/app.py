import os
import logging
import binascii

# Import utilities
from fsdicts import *
from runtypes import typechecker, Text, Optional
from guardify import *

# Import internal router
from router import router

from globals import DATABASE, AUTHORITY
from composer import Deployment

# Setup the logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Read the temporary token validity
ACCESS_TOKEN_VALIDITY = int(os.environ.get("ACCESS_TOKEN_VALIDITY", 60 * 10))
PERMANENT_TOKEN_VALIDITY = int(os.environ.get("PERMANENT_TOKEN_VALIDITY", 10 * 60 * 60 * 24 * 365))


@typechecker
def PasswordType(password):
    # Convert the password to text
    password = Text(password)
    
    # Compare password to preset variable
    if password != os.environ.get("PASSWORD"):
        raise ValueError("Password is incorrect")
    
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

def deployment_from_token(token):
    # Return the deployment
    return DeploymentType(token.contents["id"])

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


@router.post("/api/pubkey", type_password=PasswordType, type_deployment=DeploymentType)
def pubkey(password, deployment):
    # Read the SSH key
    return deployment.pubkey


@router.post("/api/access", type_password=PasswordType, type_deployment=DeploymentType)
def access(password, deployment):
    # Create temporary access token
    token, _ = AUTHORITY.issue("Temporary access token for %s" % deployment.id, dict(id=deployment.id), [
        # Information
        "info", 
        "logs", 
        "status", 
        # Source management
        "pull", 
        "clone",
        "update", 
        # Runtime management
        "stop", 
        "start", 
        "restart",
        # Deployment management
        "reset",
        "destroy",
    ], ACCESS_TOKEN_VALIDITY)

    # Return the created token
    return token


@router.post("/api/token", type_password=PasswordType, type_deployment=DeploymentType)
def token(password, deployment):
    # Issue token with general permissions
    general, _ = AUTHORITY.issue(str(), dict(id=deployment.id), [
        # Information
        "logs",
        "status",
        # Source management
        "pull",
        "update",
        # Runtime management
        "stop",
        "start",
        "restart",
    ], PERMANENT_TOKEN_VALIDITY)

    # Issue token with webhook permission
    webhook, _ = AUTHORITY.issue(str(), dict(id=deployment.id), ["webhook"], PERMANENT_TOKEN_VALIDITY)

    # Return the created tokens
    return dict(general=general, webhook=webhook)


@router.post("/api/edit", type_password=PasswordType, type_deployment=DeploymentType, type_name=Optional[Text], type_directory=Optional[Text], type_repository=Optional[Text])
def edit(password, deployment, name=None, directory=None, repository=None):
    return deployment.edit(name=name, directory=directory, repository=repository)

@router.post("/api/delete", type_password=PasswordType, type_deployment=DeploymentType)
def delete(password, deployment):
    return deployment.delete()

@router.post("/api/info", type_token=AUTHORITY.TokenType["info"])
def info(token):
    # Parse token object and get ID
    return deployment_from_token(token).information

@router.post("/api/status", type_token=AUTHORITY.TokenType["status"])
def status(token, timeout=3):
    return deployment_from_token(token).status

@router.post("/api/start", type_token=AUTHORITY.TokenType["start"])
def start(token):
    return deployment_from_token(token).start()

@router.post("/api/stop", type_token=AUTHORITY.TokenType["stop"], optional_timeout=int)
def stop(token, timeout=3):
    return deployment_from_token(token).stop(timeout=timeout)

@router.post("/api/logs", type_token=AUTHORITY.TokenType["logs"], type_tail=Optional[int])
def logs(token, tail=100):
    return deployment_from_token(token).logs(tail=tail)

@router.post("/api/pull", type_token=AUTHORITY.TokenType["pull"], type_reset=Optional[bool])
def pull(token, reset=False):
    return deployment_from_token(token).pull(reset=reset)

@router.post("/api/clone", type_token=AUTHORITY.TokenType["clone"])
def clone(token):
    return deployment_from_token(token).clone()

@router.post("/api/destroy", type_token=AUTHORITY.TokenType["destroy"],type_timeout=Optional[int])
def destroy(token, timeout=None):
    return deployment_from_token(token).destroy(timeout)

@router.post("/api/restart", type_token=AUTHORITY.TokenType["stop", "start"], type_timeout=Optional[int])
def restart(token, timeout=None):
    return stop(token, timeout) + start(token)

@router.post("/api/reset", type_token=AUTHORITY.TokenType["destroy", "start"], type_timeout=Optional[int])
def reset(token, timeout=None):
    return destroy(token, timeout) + start(token)