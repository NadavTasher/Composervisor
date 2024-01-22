import os

from globals import DATABASE, AUTHORITY
from runtypes import typechecker, Schema, Text


# Create token type
TokenType = AUTHORITY.TokenType

# Create item type
Item = Schema[dict(name=Text, directory=Text, repository=Text)]


@typechecker
def Password(password):
    # Convert the password to text
    password = Text(password)
    
    # Compare password to preset variable
    if password != os.environ.get("PASSWORD"):
        raise ValueError("Password is incorrect")
    
	# Return the password
    return password


@typechecker
def Identifier(identifier):
    # Convert the identifier to text
    identifier = Text(identifier)

    # Make sure identifier exists in database
    if identifier not in DATABASE:
        raise ValueError("%r is not a deployment" % identifier)
    
    # Return the converted identifier
    return identifier