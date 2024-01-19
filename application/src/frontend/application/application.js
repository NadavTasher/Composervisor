async function checkPassword() {
	// Make sure password exists
	if (!localStorage.password) {
		// Read password from prompt
		const password = await Prompt.dialog("Please enter your password", "Password");

		// Check password
		try {
			// Make a simple API call
			await API.call("list", {
				password: password,
			});

			// Save password
			localStorage.password = password;
		} catch (ignored) {
			// Show error dialog
			await Alert.dialog("Entered password is incorrect!");

			// Reload page
			location.reload();
		}
	}
}