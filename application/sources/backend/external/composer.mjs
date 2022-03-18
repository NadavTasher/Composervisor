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
	execute,
	join,
	render,
	random
} from "../internal/utilities.mjs";
import { 
	PRIVATE,
	PUBLIC,
	CREATE_KEY_COMMAND,
	REPOSITORY,
	CREATE_PATH_COMMAND,
	DELETE_PATH_COMMAND,
	GIT_COMMAND,
	COMPOSE_TAIL,
	COMPOSE_TIMEOUT,
	COMPOSE_COMMAND,
	START_DEPLOYMENT_COMMAND,
	STOP_DEPLOYMENT_COMMAND,
	STATUS_DEPLOYMENT_COMMAND,
	DESTROY_DEPLOYMENT_COMMAND,
	RESET_DEPLOYMENT_COMMAND,
	RESTART_DEPLOYMENT_COMMAND,
	DELETE_DEPLOYMENT_COMMAND,
	UPDATE_DEPLOYMENT_COMMAND,
	CREATE_DEPLOYMENT_COMMAND
} from "./constants.mjs";

// Create database files
const Property = new File("property.json");
const Database = new File("database.json");

// Load properties from file
const properties = Property.read({});

// Make sure properties contain the token secret
if (!properties.secret) {
	// Generate the token secret
	properties.secret = random(16);

	// Save the modified properties
	Property.write(properties);
}

// Create token validation object
const Token = new Authority(properties.secret);

// Export function to read files
export function read(path) {
	return fs.readFileSync(path).toString();
};

// Export function to write files
export function write(path, data) {
	return fs.writeFileSync(path, data);
};

// Export function to validate password
export async function validate(password) {
	// Sleep for a second
	await new Promise(resolve => setTimeout(resolve, 1000));

	// Validate the password
	return (password === process.env.PASSWORD);
};

// Export function to fetch a deployment
export function deployment(token, action, exists = true) {
	// Validate token
	const id = Token.validate(token, [ action ]).contents().id;

	// Read the database
	const database = Database.read({});

	// Make sure the ID exists
	if (!database[id])
		throw new Error("Deployment does not exist");

	// Read the deployment
	const entry = database[id];

	// Make sure the deployment has all required properties
	if (!entry.repository)
		throw new Error("Deployment does not have a repository");
	if (!entry.directory)
		throw new Error("Deployment does not have a directory");

	// Make sure the repository directory exists
	const repository = fs.existsSync(join(OUTPUT, id, REPOSITORY));
	
	// Make sure the repository directory exists (or not)
	if (exists && !repository)
		throw new Error("Deployment repository is not initialized");
	if (!exists && repository)
		throw new Error("Deployment repository is already initialized");

	// Return the deployment
	return {
		id: id,
		path: join(OUTPUT, id),
		directory: entry.directory,
		repository: entry.repository,
	};
};

// Export all permissions
export const PERMISSIONS = [
	"pull",
	"clone",
	"start",
	"stop",
	"reset",
	"status",
];

// Export all routes
export default {
	composer: {
		list: {
			handler: async () => {
				// Return the database
				return Database.read({});
			},
			parameters: {
				password: validate,
			}
		},
		token: {
			handler: async (parameters) => {
				// Read the database
				const database = Database.read({});

				// Make sure deployment exists
				if (!database[parameters.id])
					throw new Error("Deployment does not exist");

				// Make sure all permissions exist in the list
				for (const permission of parameters.permissions)
					if (!PERMISSIONS.includes(permission))
						throw new Error(`Permission ${permission} does not exist`);

				// Create action token
				return Token.issue(`Permenant access token for ${parameters.id}`, { id: parameters.id }, parameters.permissions, new Date().getTime() + 60 * 60 * 24 * 365 * 10 * 1000);
			},
			parameters: {
				// Deployment ID
				id: "string",
				// Token permissions
				permissions: "array",
				// Password authorization
				password: validate,
			}
		},
		fetch: {
			handler: async (parameters) => {
				// Read the database
				const database = Database.read({});

				// Make sure deployment exists
				if (!database[parameters.id])
					throw new Error("Deployment does not exist");

				// Read the deployment
				const deployment = database[parameters.id];

				// Set the public key in the deployment object
				deployment.key = read(join(OUTPUT, parameters.id, PUBLIC));

				// Create temporary action token
				deployment.token = Token.issue(`Temporary access token for ${parameters.id}`, { id: parameters.id }, PERMISSIONS, new Date().getTime() + 60 * 10 * 1000);

				// Return the deployment
				return deployment;
			},
			parameters: {
				// Deployment ID
				id: "string",
				// Password authorization
				password: validate,
			}
		},
		create: {
			handler: async (parameters) => {
				// Create new entry in the database
				const database = Database.read({});

				// Generate a new ID
				const id = random(8);

				// Create deployment folder
				await execute(render(CREATE_PATH_COMMAND, {
					path: join(OUTPUT, id)
				}));

				// Generate a new ssh key pair
				await execute(render(CREATE_KEY_COMMAND, {
					id: id,
					path: join(OUTPUT, id)
				}));

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

				// Return the generated ID
				return id;
			},
			parameters: {
				// Password authorization
				password: validate,
			}
		},
		modify: {
			handler: async (parameters) => {
				// Read the database
				const database = Database.read({});

				// Make sure deployment exists
				if (!database[parameters.id])
					throw new Error(`Deployment does not exist`);

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
				// Deployment ID
				id: "string",
				// Deployment name
				name: "string",
				// Deployment directory
				directory: "string",
				// Deployment repository
				repository: "string",
				// Password authorization
				password: validate
			}
		},
		delete: {
			handler: async (parameters) => {
				// Read the database
				const database = Database.read({});

				// Make sure deployment exists
				if (!database[parameters.id])
					throw new Error(`Deployment does not exist`);

				// TODO: delete deployment that has not been cloned

				// Destroy the deployment
				const output = await execute(render(DESTROY_DEPLOYMENT_COMMAND, {
					id: parameters.id,
					path: join(OUTPUT, parameters.id),
				}));

				// Delete deployment from database
				delete database[parameters.id];

				// Write database to file
				Database.write(database);

				// Return the destroyed deployment output
				return output;
			},
			parameters: {
				// Deployment ID
				id: "string",
				// Password authorization
				password: validate
			}
		},
	},
	action: {
		pull: {
			handler: async (parameters) => {
				// Pull the repository
				return await execute(render(UPDATE_DEPLOYMENT_COMMAND, deployment(parameters.token, "pull")));
			},
			parameters: {
				token: "string"
			}
		},
		clone: {
			handler: async (parameters) => {
				// Clone the repository
				return await execute(render(CREATE_DEPLOYMENT_COMMAND, deployment(parameters.token, "clone", false)));
			},
			parameters: {
				token: "string"
			}
		},
		start: {
			handler: async (parameters) => {
				// Start the deployment
				return await execute(render(START_DEPLOYMENT_COMMAND, deployment(parameters.token, "start")));
			},
			parameters: {
				token: "string"
			}
		},
		stop: {
			handler: async (parameters) => {
				// Stop the deployment
				return await execute(render(STOP_DEPLOYMENT_COMMAND, deployment(parameters.token, "stop")));
			},
			parameters: {
				token: "string"
			}
		},
		reset: {
			handler: async (parameters) => {
				// Reset the deployment
				return await execute(render(RESET_DEPLOYMENT_COMMAND, deployment(parameters.token, "reset")));
			},
			parameters: {
				token: "string"
			}
		},
		status: {
			handler: async (parameters) => {
				// Fetch deployment status
				return await execute(render(STATUS_DEPLOYMENT_COMMAND, deployment(parameters.token, "status")));
			},
			parameters: {
				token: "string"
			}
		}
	}
};