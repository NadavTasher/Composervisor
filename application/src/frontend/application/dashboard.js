window.addEventListener("load", async function () {
	// Load the modules
	await Module.load("API", "UI", "GUI");

	// Make sure password is set
	await checkPassword();

	// Load the page
	await load();

	// Show the page
	UI.show("dashboard");
});

async function load() {
	try {
		await Progress.screen("Loading dashboard...", loadDashboard());
	} catch (error) {
		// Display the error
		await Alert.dialog(error);

		// Redirect to dashboard
		window.location.href = "/";
	}
}

async function loadDashboard() {
	// Add action listeners to the buttons
	UI.find("dashboard-new").onclick = async () => {
		// Create new deployment and display editing page
		const identifier = await Progress.screen(
			"Creating new deployment...",
			API.call("new", {
				password: localStorage.password,
			})
		);

		// Go to settings
		window.location.href = `/settings?identifier=${encodeURIComponent(identifier)}`;
	};

	// Get list of deployments
	const deployments = await API.call("list", {
		password: localStorage.password,
	});

	// Clear list of deployments
	UI.clear("dashboard-list");

	// Sort deployment entries by name
	const entries = Object.entries(deployments).sort(([a, A], [b, B]) => {
		// Compare deployment names
		return String(A).localeCompare(String(B));
	});

	// Add deployments to the list
	for (const [identifier, name] of entries) {
		// Create deployment element from template
		const element = UI.populate("dashboard-deployment", { name });

		// Add item to the list
		UI.find("dashboard-list").appendChild(element);

		// Load status asynchronously
		loadDeployment(element, identifier);
	}

	// Write the summary
	UI.write("dashboard-summary", `${Object.keys(deployments).length} managed deployments`);
}

async function loadDeployment(element, identifier) {
	// Generate a temporary access token
	const token = await API.call("access", {
		identifier: identifier,
		password: localStorage.password,
	});

	// Add event listeners to the buttons
	element.find("deployment").href = `/deployment?token=${encodeURIComponent(token)}`;
	element.find("settings").href = `/settings?identifier=${encodeURIComponent(identifier)}`;

	// Find status element
	const status = element.find("status");

	try {
		// Fetch status of deployment
		const DEPLOYMENTS_DIRECTORY = await API.call("status", { token });

		// Check if status has length
		if (DEPLOYMENTS_DIRECTORY.length === 0) throw new Error();

		// Update status
		status.style.color = "lightgreen";
		UI.write(status, "Deployment is running");
	} catch (error) {
		// Update status
		status.style.color = "red";
		UI.write(status, "Deployment is not running");
	}
}