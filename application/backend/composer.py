import os
import json
import logging

from router import router

from constants import *
from database import Database

from puppy.typing.check import kwargcheck
from puppy.typing.types import Literal, Optional
from puppy.token.autority import Authority

DATABASE = Database("/opt/database.json")
AUTHORITY = Authority(os.environ.get("SECRET"))

def validate_deployment(function):
    @kwargcheck(token=str)
    def wrapper(request, **kwargs):
        pass
    return function

@router.post("/list")
@kwargcheck(password=Literal[os.environ.get("PASSWORD")])
def list_deployments(request, password):
    return DATABASE.read()

