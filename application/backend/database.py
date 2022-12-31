import os
import json
import bunch


class Database(object):

    def __init__(self, path):
        self.path = path

    def get(self, identifier):
        # Read the database
        data = self.read()

        # Check if identifier exists
        assert identifier in data.keys(), "No such ID"

        # Read and return bunch
        return bunch.Bunch(data[identifier])

    def set(self, identifier, dictionary):
        # Read the database
        data = self.read()

        # Update the dictionary
        data[identifier] = dict(dictionary)

        # Save the dictionary
        self.write(data)

    def remove(self, identifier):
        # Read the database
        data = self.read()

        # Update the dictionary
        del data[identifier]

        # Save the dictionary
        self.write(data)

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
