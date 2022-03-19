// Import modules
import fs from "fs";
import process from "process";

// Import utilities
import { 
	OUTPUT
} from "../internal/utilities/file.mjs";
import { 
	File,
	Authority,
	join,
	render,
	random,
	execute,
} from "../internal/utilities.mjs";
import { 
	PUBLIC,
	REPOSITORY,
	KEY_COMMAND,
	MKDIR_COMMAND,
	RMDIR_COMMAND,
	START_COMMAND,
	STOP_COMMAND,
	LOG_COMMAND,
	STATUS_COMMAND,
	DESTROY_COMMAND,
	RESET_COMMAND,
	RESTART_COMMAND,
	PULL_COMMAND,
	CLONE_COMMAND,
	UPDATE_COMMAND,
} from "./constants.mjs";

// Create token validation object
const Token = new Authority(process.env.SECRET);

// Create database file
const Database = new File("database.json");

// Function to validate password
function validate(password) {
	// Validate the password
	return (password === process.env.PASSWORD);
};

// Function to read a deployment
function deployment(id) {
	// Read the database
	const database = Database.read({});

	// Make sure the ID exists
	if (!database[id])
		throw new Error("Deployment does not exist");

	// Read the deployment
	const entry = database[id];

	// Add the path and ID to the entry
	entry.id = id;
	entry.path = join(OUTPUT, id);

	// Return the deployment
	return entry;
}

// Create all route definitions
const ACTIONS = {
	// Management actions
	"pull": [PULL_COMMAND, true],
	"clone": [CLONE_COMMAND, false],
	"update": [UPDATE_COMMAND, true],
	"destroy": [DESTROY_COMMAND, true],
	// State actions
	"stop": [STOP_COMMAND, true],
	"start": [START_COMMAND, true],
	"reset": [RESET_COMMAND, true],
	"restart": [RESTART_COMMAND, true],
	// Status actions
	"log": [LOG_COMMAND, true],
	"status": [STATUS_COMMAND, true],
};

// Stores action routes
const ROUTES = {
	// Management routes
	composer: {
		new: {
			handler: async (parameters) => {
				// Create new entry in the database
				const database = Database.read({});

				// Generate a new ID
				const id = random(8);

				// Create database entry
				database[id] = {
					// Deployment name
					name: null,
					// Deployment directory (inside of repository)
					directory: null,
					// Deployment repository (address of repository)
					repository: null,
				};

				// Write database to file
				Database.write(database);

				// Fetch the deployment object
				const entry = deployment(id);

				// Create deployment folder
				await execute(render(MKDIR_COMMAND, entry));

				// Generate a new SSH key pair
				await execute(render(KEY_COMMAND, entry));

				// Return the generated ID
				return id;
			},
			parameters: {
				password: validate,
			}
		},
		list: {
			handler: async () => {
				// Return the database
				return Database.read({});
			},
			parameters: {
				password: validate,
			}
		},
		fetch: {
			handler: async (parameters) => {
				// Fetch the deployment object
				const entry = deployment(parameters.id);

				// Add public key
				entry.key = fs.readFileSync(
					join(OUTPUT, parameters.id, PUBLIC)
				).toString();

				// Add temporary token
				entry.token = Token.issue(
					// Token name
					`Temporary access token for ${parameters.id}`,
					// Token contents
					{
						id: parameters.id
					},
					// Token permissions
					Object.keys(ACTIONS),
					// Token expiration
					new Date().getTime() + 60 * 10 * 1000
				);

				// Return the deployment
				return entry;
			},
			parameters: {
				id: deployment,
				password: validate,
			}
		},
		token: {
			handler: async (parameters) => {
				// Issue the token
				return Token.issue(
					// Token title
					`Permenant access token for ${parameters.id}`,
					// Token contents
					{
						id: parameters.id
					},
					// Token permissions
					[
						"pull",
						"stop",
						"start",
						"update",
						"restart",
					],
					// Token expiration
					0,
				);
			},
			parameters: {
				id: deployment,
				password: validate,
			}
		},
		update: {
			handler: async (parameters) => {
				// Read the database
				const database = Database.read({});

				// Update database entry
				database[parameters.id] = {
					// Deployment name
					name: parameters.name,
					// Deployment directory (inside of repository)
					directory: parameters.directory,
					// Deployment repository (address of repository)
					repository: parameters.repository,
				};

				// Write database to file
				Database.write(database);

				// Return the updated database
				return null;
			},
			parameters: {
				name: "string",
				directory: "string",
				repository: "string",
				id: deployment,
				password: validate
			}
		},
		delete: {
			handler: async (parameters) => {
				// Fetch the deployment object
				const entry = deployment(parameters.id);

				// Check if repository has been cloned
				if (fs.existsSync(join(OUTPUT, parameters.id, REPOSITORY))) {
					// Try destoying the deployment
					try {
						// Destroy the deployment
						await execute(render(DESTROY_COMMAND, entry));
					} catch (error) {
						// Ignore errors
					}
				}

				// Try deleting the deployment folder
				try {
					// Delete the deployment folder
					await execute(render(RMDIR_COMMAND, entry));
				} catch (error) {
					// Ignore errors
				}

				// Read the database
				const database = Database.read({});

				// Delete deployment from database
				delete database[parameters.id];

				// Write database to file
				Database.write(database);

				// Return null
				return null;
			},
			parameters: {
				id: deployment,
				password: validate
			}
		},
	},
	action: {},
};

// Loop over all actions and create route functions
for (const [action, [command, exists]] of Object.entries(ACTIONS)) {
	// Create the route function
	ROUTES.action[action] = {
		handler: async (parameters) => {
			// Validate token
			const id = Token.validate(parameters.token, [ action ]).contents().id;

			// Read the deployment
			const entry = deployment(id);

			// Make sure the deployment has a repository property
			if (!entry.repository)
				throw new Error("Deployment does not have a repository");
			
			// Make sure the deployment has a directory property
			if (!entry.directory)
				throw new Error("Deployment does not have a directory");

			// Make sure the repository directory exists
			const repository = fs.existsSync(join(OUTPUT, id, REPOSITORY));
			
			// Make sure the repository directory exists
			if (exists)
				if (!repository)
					throw new Error("Deployment repository is not initialized");

			// Make sure the repository directory does not exist
			if (!exists)
				if (repository)
					throw new Error("Deployment repository is already initialized");

			// Execute the command
			return await execute(render(command, entry));
		},
		parameters: {
			token: "string",
		}
	}
}

// Export all routes
export default ROUTES;