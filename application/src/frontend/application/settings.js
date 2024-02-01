window.addEventListener("load", async function () {
	// Load the modules
	await Module.load("API", "UI", "GUI");

	// Make sure password is set
	await checkPassword();

	// Check query parameters
	const parameters = new URLSearchParams(window.location.search);

	// Load the page
	await load(parameters.get("deployment"));

	// Show the page
	UI.show("settings");
});

async function load(deployment) {
	try {
		await Progress.screen("Loading settings...", loadSettings(deployment));
	} catch (error) {
		// Display the error
		await Alert.dialog(error);

		// Redirect to dashboard
		window.location.href = "/";
	}
}

async function loadSettings(deployment) {
	// Fetch a new temporary access token
	const token = await API.call("access", {
		deployment: deployment,
		password: localStorage.password,
	});

	// Fetch deployment key
	const pubkey = await API.call("pubkey", {
		deployment: deployment,
		password: localStorage.password,
	});

	// Fetch deployment information
	const information = await API.call("info", { token });

	// Add data to the editor
	UI.write("settings-key", pubkey || "Missing SSH Key");
	UI.write("settings-name", information.name || `Unnamed deployment - ${deployment}`);
	UI.write("settings-directory", information.directory || ".");
	UI.write("settings-repository", information.repository || "git@github.com:NadavTasher/Composervisor.git");

	// Add event listeners to the buttons
	for (const action of ["edit", "token", "delete"]) {
		UI.find(`settings-${action}`).onclick = async () => {
			try {
				// Create the parmeters
				const parameters = {
					deployment: deployment,
					password: localStorage.password,
				};

				// Prompt the user to confirm
				if (action === "delete") {
					// Wait for prompt
					const answer = await Prompt.dialog(`Do you want to ${action} the deployment?`, `Enter 'yes' to ${action}`);

					// Check answer and compare it
					if (answer.toLowerCase() !== "yes")
						// Throw error for cancellation
						throw new Error("User cancelled the action");
				} else if (action === "edit") {
					// Add editing parameters
					parameters["name"] = UI.read("settings-name");
					parameters["directory"] = UI.read("settings-directory");
					parameters["repository"] = UI.read("settings-repository");
				}

				// Execute action
				const result = await Progress.drawer("Executing action...", API.call(action, parameters));

				// Check if result exists and needs to be displayed
				if (result) {
					if (action === "token") {
						// Create links to display
						const links = [`${window.location.origin}/deployment?token=${encodeURIComponent(result.general)}`, `${window.location.origin}/api/webhook?token=${encodeURIComponent(result.webhook)}`];

						// Display links in dialog
						await Alert.dialog(links.join("\n"));
					} else {
						// Display result in dialog
						await Alert.dialog(result);
					}
				} else {
					// Go to dashboard
					window.location.href = "/";
				}
			} catch (error) {
				// Show error dialog
				await Alert.dialog(error || "An error has occurred");
			}
		};
	}
}
