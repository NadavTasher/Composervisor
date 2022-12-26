import os
import json

class Database(object):
    def __init__(self, path):
        self.path = path

    def read(self, default=dict()):
        # Make sure path exists
        if not os.path.exists(self.path):
            return default

        # Read from file
        with open(self.path, "r") as database:
            return json.load(database)

    def write(self, data):
        # Write to file
        with open(self.path, "w") as database:
            json.dump(data, database)