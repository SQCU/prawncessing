# TO-FUTURE-GEMINIS.md

This document outlines immediate next steps and success/failure rubrics for a Gemini agent operating within this project context.

## Immediate Next Steps & Rubric

### 1. Understand the Project Structure and Core Functionality

*   **Description:** Familiarize yourself with the overall directory structure, key files, and the primary purpose of this project (e.g., video processing, DCT, server-client interactions).
*   **Action:**
    *   Review `README.md` for project overview.
    *   Examine `package.json` and `pyproject.toml` for dependencies and scripts.
    *   Quickly scan `main.py`, `index.html`, `sketch.js`, `dct.js` for core logic entry points.
    *   Look at `GEMINI.md` for previous agent notes and context.
*   **Success:**
    *   Can articulate the project's main goal and its key components (e.g., "This project appears to be a real-time video signal processor focusing on DCT-based operations and datamoshing, with both Python and JavaScript components.").
    *   Can identify the primary language(s) and framework(s) used.
    *   Can locate common entry points for running the application or tests.
*   **Failure:**
    *   Cannot describe the project's purpose or key technologies.
    *   Unable to find main application files or configuration.

### 2. Identify Common Development Workflows (Build, Test, Run)

*   **Description:** Determine how to build, test, and run the various components of the project. This is crucial for verification and implementation.
*   **Action:**
    *   Search for common build/run scripts (e.g., `start.sh`, `depload.sh`, `package.json` scripts, `Makefile`).
    *   Look for test files and test runners (e.g., `test_*.py`, `package.json` test scripts, `pytest` usage).
    *   Identify linting/formatting commands if present.
*   **Success:**
    *   Can execute a basic "run" command for the application (if applicable).
    *   Can execute the project's test suite (if applicable) and understand its output.
    *   Can identify commands for linting/type-checking.
*   **Failure:**
    *   Cannot find any clear way to run or test the project.
    *   Attempts to run/test fail without clear reasons.

### 3. Establish Communication and Interaction Protocols

*   **Description:** Understand how to effectively communicate with the user and manage the interaction flow.
*   **Action:**
    *   Adhere to the "Tone and Style (CLI Interaction)" guidelines from the initial prompt.
    *   Prioritize safety and explain critical commands.
    *   Confirm ambiguous requests.
*   **Success:**
    *   User feedback indicates clear, concise, and helpful interactions.
    *   No unintended system modifications occur due to un-explained commands.
    *   User feels in control of the process.
*   **Failure:**
    *   User expresses confusion or frustration with responses.
    *   Commands are executed without proper explanation or confirmation.
    *   Interaction becomes verbose or deviates from the CLI tone.

### 4. Utilize Tools Effectively and Safely

*   **Description:** Leverage the provided tools (`read_file`, `write_file`, `run_shell_command`, `glob`, `search_file_content`, `replace`, etc.) appropriately and safely.
*   **Action:**
    *   Always use absolute paths for file operations.
    *   Use `read_file` or `read_many_files` to understand file content before modifying.
    *   Explain `run_shell_command` for modifying commands.
    *   Use `glob` and `search_file_content` for initial exploration.
*   **Success:**
    *   Tools are used efficiently to gather information and perform actions.
    *   No tool-related errors due to incorrect parameters (e.g., relative paths).
    *   Modifications are precise and targeted.
*   **Failure:**
    *   Frequent tool errors.
    *   Inefficient use of tools (e.g., reading entire large files when only a few lines are needed).
    *   Unintended side effects from modifications.

### 5. Maintain Git Repository Integrity

*   **Description:** Ensure all changes are tracked, committed appropriately, and follow project's commit conventions.
*   **Action:**
    *   Before committing, always run `git status`, `git diff HEAD`, and `git log -n 3`.
    *   Propose clear, concise commit messages.
    *   Do not push without explicit user instruction.
*   **Success:**
    *   Git status is clean after changes are applied and committed.
    *   Commit messages are well-formed and informative.
    *   User approves proposed commits.
*   **Failure:**
    *   Untracked or unstaged changes remain after a task.
    *   Commit messages are vague or do not follow conventions.
    *   Changes are pushed without user consent.