# JARVIS - Demo Recovery & Cleanup

Because JARVIS executes safely against the filesystem using the AuthorizationService, all tests run against the `FINAL_HUMAN_TEST_PACKAGE/demo` folder.

## How to Reset the Demo Environment
If the demo directory becomes cluttered after testing, follow these steps to reset the environment:

1. Close the JARVIS application.
2. In VS Code, manually delete any files generated inside the `/demo` folder.
3. Ensure `/demo` is completely empty.
4. Restart JARVIS. JARVIS will automatically detect the fresh state of the directory when VS Code regains focus.

**Note:** JARVIS does not leave hidden dotfiles, configuration scripts, or background processes inside your project directories. All runtime state is strictly confined to `~/.jarvis/runtime` on your user profile.
