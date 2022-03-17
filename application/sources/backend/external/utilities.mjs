// Import NodeJS modules
import fs from "fs";

// Function to read files
export function read(path) {
	return fs.readFileSync(path).toString();
};

// Function to write files
export function write(path, data) {
	return fs.writeFileSync(path, data);
};