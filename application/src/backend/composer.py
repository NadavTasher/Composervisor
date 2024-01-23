import os
import shutil
import contextlib
import subprocess

from globals import DATABASE

# Create some constants
DEPLOYMENTS_DIRECTORY = "/opt/deployments"
PRIVATE_KEY_NAME = "id_rsa"
PUBLIC_KEY_NAME = PRIVATE_KEY_NAME + ".pub"

class Deployment(object):

	def __init__(self, identifier):
		# Set the internal identifier
		self._identifier = identifier

		# Create deployment paths
		self._deployment_path = os.path.join(DEPLOYMENTS_DIRECTORY, self._identifier)
		self._repository_path = os.path.join(self._deployment_path, "repository")
		self._ssh_key_path = os.path.join(self._deployment_path, "id_rsa")
		self._ssh_pubkey_path = os.path.join(self._deployment_path, "id_rsa.pub")

	@property
	def id(self):
		return self._identifier

	@property
	def exists(self):
		# Check whether the deployment exists
		return self._identifier in DATABASE
	
	@property
	def cloned(self):
		# Check whether the repository was cloned
		return os.path.isdir(self._repository_path)
	
	@property
	def pubkey(self):
		# Make sure the deployment is initialized
		assert self.exists, "Deployment is not initialized"

		# Read the public key
		with open(self._ssh_pubkey_path, "r") as pubkey_file:
			return pubkey_file.read()

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
		if repository and not self.cloned:
			DATABASE[self._identifier].repository = repository

		# Return the repository object
		return DATABASE[self._identifier]
	
	def status(self):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Check whether any containers are running
		return self._compose("ps", "--quiet")
	
	def logs(self, tail=100):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Read container logs with tail
		return self._compose("logs", "--no-color", "--no-log-prefix", "--tail", str(tail))
	
	def build(self):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Build the container images
		return self._compose("build", "--pull", "--force-rm")
	
	def start(self):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Start the deployment containers
		return self._compose("up", "--no-color", "--detach")

	def stop(self, timeout=3):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Stop the deployment containers with timeout
		return self._compose("down", "--remove-orphans", "--timeout", str(timeout))

	def destroy(self):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# Stop the deployment
		self.stop()

		# Destroy the deployment by removing volumes
		return self._compose("down", "--volumes")
	
	def delete(self):
		# Check whether the repository was cloned
		if self.cloned:
			# Try destroying the deployment
			with contextlib.suppress(RuntimeError):
				self.destroy()

		# Delete the database item
		del DATABASE[self._identifier]

		# Remove the directory
		with contextlib.suppress(OSError):
			shutil.rmtree(self._deployment_path)				
	
	def pull(self, reset=False):
		# Make sure repository was cloned
		assert self.cloned, "Repository was not cloned"

		# If should reset, reset hard
		if reset:
			self._git("-C", self._repository_path, "reset", "--hard")

		# Pull from the remote
		return self._git("-C", self._repository_path, "pull")

	def clone(self):
		# Make sure repository was not cloned
		assert not self.cloned, "Repository was already cloned"

		# Clone the deployment
		repository = DATABASE[self._identifier].repository

		# Clone the git repository
		return self._git("clone", repository, self._repository_path)

	def _git(self, *args):
		# Create process and execute it
		process = subprocess.Popen(
			["git", "-c", "pull.rebase", "false", "-c", "core.sshCommand", "ssh -i %r" % self._ssh_key_path] + args,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,	
		)

		# Wait for process
		return self._wait(process)

	def _compose(self, *args):
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

		# Wait for process
		return self._wait(process)
	
	def _wait(self, process):
		# Wait for the process to complete
		stdout, stderr = process.communicate()

		# If the process didn't finish gracefully, raise exception
		if process.returncode != 0:
			raise RuntimeError(stderr)
		
		# Return the output
		return stdout