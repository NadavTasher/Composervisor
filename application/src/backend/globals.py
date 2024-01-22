import os

from fsdicts import fastdict
from guardify import Authority

# Initialize database and token generator
DATABASE = fastdict("/opt/database")
AUTHORITY = Authority(os.environ["SECRET"].encode())
