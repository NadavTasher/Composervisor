window.addEventListener("load", async function () {
	// Load the modules
	await Module.load("API", "UI", "GUI");

	// Check query parameters
	const parameters = new URLSearchParams(window.location.search);

	// Load the page
	await load(parameters.get("token"));

	// Show the page
	UI.show("deployment");
});

async function load(token) {
	try {
		await Progress.screen("Loading deployment...", loadDeployment(token));
	} catch (error) {
		// Display the error
		await Alert.dialog(error);

		// Redirect to dashboard
		window.location.href = "/";
	}
}

async function loadDeployment(token) {
	// Fetch deployment details
	const deployment = await API.call("info", { token });

	// Add data to the editor
	UI.write("deployment-name", deployment.name);

	try {
		// Fetch the status of the deployment
		const status = await API.call("status", { token });

		// Check if the status is not empty
		if (status.length === 0) throw new Error();

		// Fetch the log of the deployment
		const log = await API.call("log", { token });

		// Update log and status
		UI.write("deployment-log", log);
		UI.write("deployment-status", "Deployment is running");
	} catch (error) {
		// Update log and status
		UI.write("deployment-log", "No deployment log");
		UI.write("deployment-status", "Deployment is not running");
	}

	// Add event listener to the refresh button
	UI.find("deployment-refresh").onclick = () => load(token);

	// Add event listeners to the controls
	for (const action of ["start", "stop", "restart", "update", "clone", "reset"]) {
		UI.find(`deployment-${action}`).onclick = async () => {
			try {
				// Prompt the user to confirm
				if (action === "reset") {
					// Wait for prompt
					const answer = await Prompt.dialog(`Do you want to ${action} the deployment?`, `Enter 'yes' to ${action}`);

					// Check answer and compare it
					if (answer.toLowerCase() !== "yes")
						// Throw error for cancellation
						throw new Error("User cancelled the action");
				}

				// Execute action
				await Progress.drawer("Executing action...", API.call(action, { token }));

				// Reload the viewer
				await load(token);
			} catch (error) {
				// Show error dialog
				await Alert.dialog(error || "An error has occurred");
			}
		};
	}
}