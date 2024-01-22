import os
import subprocess

from globals import DATABASE

# Create some constants
DEPLOYMENTS_DIRECTORY = "/opt/deployments"
PRIVATE_KEY_NAME = "id_rsa"
PUBLIC_KEY_NAME = PRIVATE_KEY_NAME + ".pub"

REPOSITORY_DIRECTORY_NAME = "repository"
TIMEOUT = "3"

def execute_git(identifier, *args):
	return subprocess.Popen(
		["git", "-c", "pull.rebase", "false", "-c", "core.sshCommand", "ssh -i %r" % os.path.join(DEPLOYMENTS_DIRECTORY, identifier, PRIVATE_KEY_NAME)] + args,
		stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,	
	)

def execute_docker_compose(identifier, *args):
	

class Deployment(object):

	def __init__(self, identifier):
		# Set the internal identifier
		self._identifier = identifier

		# Create deployment paths
		self._deployment_path = os.path.join(DEPLOYMENTS_DIRECTORY, self._identifier)
		self._repository_path = os.path.join(self._deployment_path, REPOSITORY_DIRECTORY_NAME)
		self._ssh_key_path = os.path.join(self._deployment_path, "id_rsa")
		self._ssh_pubkey_path = os.path.join(self._deployment_path, "id_rsa.pub")

		# Initialize the deployment
		if not self.exists:
			self.initialize()

	@property
	def exists(self):
		# Make sure identifier exists
		return self._identifier in DATABASE

	def initialize(self):
		# Make sure not already initialized
		assert not self.exists, "Deployment is already initialized"

		# Initialize the object
		DATABASE[self._identifier] = dict(name=None, directory=None, repository=None)

		# Set the default parameters
		self.edit("Unnamed deployment - %r" % self._identifier, "bundle", "git@github.com/NadavTasher/Webhood.git")

		# Create directory for deployment
		os.makedirs(self._deployment_path)

		# Create SSH access key for deployment
		subprocess.check_call(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", PRIVATE_KEY_NAME, "-N", str(), "Deployment key for %s" % self._identifier], cwd=self._directory)

	def edit(self, name=None, directory=None, repository=None):
		# Make sure the deployment is initialized
		assert self.exists, "Deployment is not initialized"

		# Update name if required
		if name:
			DATABASE[self._identifier].name = name

		# Update directory if required
		if directory:
			DATABASE[self._identifier].directory = directory

		# Update repository if required
		if repository:
			DATABASE[self._identifier].repository = repository

		# Return the repository object
		return DATABASE[self._identifier]
	
	def build(self, detach=False):
		return self._compose("build", "--pull", "--force-rm", detach=detach)
	
	def start(self, detach=False):
		return self._compose("up", "--no-color", "--detach", detach=detach)

	def stop(self, detach=False):
		return self._compose("down", "--remove-orphans", "--timeout", "3", detach=detach)

	def destroy(self, detach=False):
		# Stop the deployment
		self.stop()

		# Destroy the deployment
		return self._compose("down", "--volumes", detach=detach)

	def _compose(self, *args, detach=False):
		# Fetch the inner-repository compose directory
		inner_directory = DATABASE[self._deployment_path].directory

		# Create the compose directory
		compose_directory = os.path.join(self._repository_path, inner_directory)

		# Make sure the compose directory is a sub-directory of the repository path
		assert compose_directory.startswith(self._repository_path), "Compose directory is not a subdirectory of the deployment"

		# Make sure the compose directory exists
		assert os.path.isdir(compose_directory), "Compose directory does not exist"

		# Create process and execute it
		process = subprocess.Popen(
			["docker-compose", "--ansi", "never", "--project-name", self._identifier, "--project-directory", compose_directory] + args,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,	
		)

		# If should detach, return here
		if detach:
			return

		# Wait for the process to complete
		stdout, stderr = process.communicate()

		# If the process didn't finish gracefully, raise exception
		if process.returncode != 0:
			raise Exception(stderr)
		
		# Return the output
		return stdout
	


def build_deployment(identifier):
	# Build the deployment
	return execute_docker

def start_deployment(identifier):
	return execute_docker_compose(identifier, )

def stop_deployment(identifier):
	return execute_docker_compose(identifier, )

def pull_deployment(identifier):
	return execute_git(identifier, "-C", REPOSITORY_DIRECTORY_NAME, "pull")

def clone_deployment(identifier):
	# Fetch the git remote URL from the database
	git_remote = DATABASE[identifier].remote

	# Clone the git repository
	return execute_git(identifier, "clone", git_remote, REPOSITORY_DIRECTORY_NAME)

def update_deployment(identifier):
	# Pull and build the deployment
	return pull_deployment(identifier), build_deployment(identifier)

def update_and_restart_deployment(identifier):
	update_deployment()
	restart_deployment()
