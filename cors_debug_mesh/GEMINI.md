
---

## Environment Debugging: The Case of the Missing Playwright

A recent session involved significant time spent debugging a `ModuleNotFoundError: No module named 'playwright'` error, even after `uv pip install playwright` reported a successful installation. This documentation clarifies the cause and the required operational procedure to prevent this in the future.

### The Problem

The `pytest` command failed because it could not find the `playwright` module. This occurred because the command was executed in the system's global Python environment. Meanwhile, the `playwright` package had been correctly installed by `uv` into the project-specific virtual environment located at `./.venv`. The global environment has no knowledge of the packages installed inside the project's virtual environment.

### The Solution: Virtual Environment Activation

To resolve this, the project's virtual environment must be **activated** before running any Python-related tools or scripts. Activation configures the current shell session to use the interpreter and packages installed inside the `.venv` directory, ensuring that commands like `pytest` can find their necessary dependencies.

### Call to Action: Always Activate the Environment

**For all future operations:** Before running any Python-related commands (e.g., `python`, `pip`, `pytest`, `uv`), you **MUST** first activate the virtual environment using the following command:

```bash
source .venv/bin/activate
```

This ensures that all subsequent commands operate within the correct, isolated project environment, preventing dependency and module-not-found errors.
