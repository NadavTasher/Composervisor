import os

from fsdicts import localdict
from guardify import Authority

# Initialize database
DATABASE = localdict("/opt/database")

# Initialize action queue
QUEUE, RESULTS = localdict("/opt/queue"), localdict("/opt/results")

# Initialize token generator
AUTHORITY = Authority(os.environ["SECRET"].encode())
