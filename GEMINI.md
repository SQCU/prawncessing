# ABSOLUTELY CRITICAL: ALWAYS USE THE UV VIRTUAL ENVIRONMENT

**This project uses `uv` for Python environment and package management. Under no circumstances should you use the system's global Python environment or install packages globally. All Python-related commands (`python`, `pip`, `pytest`, `uv`, etc.) MUST be run within the activated virtual environment.**

To activate the environment, run: `source .venv/bin/activate`

---

## Zone.Identifier File Cleanup

### Issue

The project directory contained numerous `*:Zone.Identifier` files. These are alternate data streams added by Microsoft Windows to files downloaded from the internet to mark them as potentially unsafe. 

### Resolution

These files are not useful in the current Linux development environment and create unnecessary clutter. I have removed all existing `*:Zone.Identifier` files and created a shell script, `scrub_zone_identifiers.sh`, to automate their removal in the future.

---

## Project Checklists

Multiple checklist files (e.g., `checklist-prawn.md`, `checklist-zqrk8.md`) exist in the project root. These are historical artifacts from previous agent interactions and should be considered a canon of past work, not a single, consolidated project plan. The most recent checklist is typically named with a session date, e.g., `checklist-session-20250627.md`. Checklists are stored at a file granularity and will not be consolidated into a single file.

---

## The "Baton Pass" Protocol (v2 - Live Tracing)

**CRITICAL REMINDER: All Python-related commands must be executed within the activated `uv` virtual environment (`source .venv/bin/activate`).**

This protocol governs all agent interactions to ensure clear, consistent, and incremental progress. It creates a live trace of each session, providing valuable feedback even if the session is interrupted.

### 1. Session Priming & Live File Creation
*   **Situating Instruction:** Every session begins with a high-level goal from the user.
*   **Live Handoff File:** The agent's *first action* is to create a new, timestamped handoff report in the `handoffs/` directory (e.g., `handoffs/20250627_154500.md`). This file serves as a live log for the session.
*   **Log the Goal:** The agent immediately writes the `Session Goal` (the user's instruction) into this new file.

### 2. The Work Sprint
*   **Grounding:** The agent reads `GEMINI.md` and the primary `checklist.md` to ground itself.
*   **Formulate & Log Plan:** The agent formulates a plan of 3-6 concrete actions. It writes this plan to the `Plan` section of the live handoff file *before* requesting approval.
*   **Approval:** The plan is presented to the user for approval.

### 3. Execution & Live Logging
*   **Execute & Log Actions:** As the agent successfully completes each action from the plan, it appends a summary of the action and its outcome to the `Work Completed` section of the live handoff file.

### 4. The "Baton": Finalizing the Handoff Report
*   **Completion:** Once the work sprint is complete, the agent finalizes the handoff report by adding:
    *   **Progress Report:** A brief summary of the progress made.
    *   **Next Steps:** 2-3 specific, actionable recommendations for the *next* agent session.
    *   **Blockers & Questions:** Any issues that arose or questions that need to be addressed.

### 5. Checklist & Context Reset
*   **Update:** The agent updates the main `checklist.md` to reflect the completed work.
*   **Commit Handoff:** The agent **must** ensure the session's handoff report (`handoffs/<timestamp>.md`) is staged and committed to the Git repository. This is not optional and serves as a permanent record of the work performed.
*   **Reset:** The agent's final act is to announce the completion of the handoff report and checklist update, and then request a full context reset from the user.

---

## GEMINI Analysis Workflow Prompt

**Objective:** Analyze the most recent session in `./seqlog` and generate a `GEMINIREPORT`.

1.  **Identify Most Recent Session:** List the `meta_*.json` files in `./seqlog`. Read them and identify the one with the latest `sessionTimestamp`.
2.  **Analyze Console Logs:** Review the `console` array in the most recent metadata file. Look for any entries with `level: 'error'`. 
3.  **Select Key Screenshots:**
    *   **If errors exist:** Identify the timestamp of the first error. Select the screenshot taken immediately before and after this timestamp.
    *   **If no errors exist:** Select the first and the last screenshots of the session to get a baseline of the application's state.
4.  **Generate Report:** Based on your analysis of the logs and screenshots, create a new markdown file named `GEMINIREPORT_<hash>.md` (where `<hash>` is the session's code hash). The report should include:
    *   A summary of the session.
    *   An analysis of any errors found.
    *   Observations from the selected screenshots.
    *   A conclusion about the session's success or failure.
5.  **Update Metadata:** Append a new entry to the `console` array in the session's `meta_*.json` file. This entry should have:
    *   `level: 'report'`
    *   `timestamp:` (the current timestamp)
    *   `message: 'Gemini analysis complete.'`
    *   `report_file: 'GEMINIREPORT_<hash>.md'`

---

## Operational Guidelines for Gemini

- **File Modification Policy:** Only modify existing files that are tracked in the Git history. Avoid making direct edits to untracked files or reference code samples, as this can introduce regressions and bypass version control.
- **Security Check during Git Operations:** Always verify that environment files (e.g., `.env`) or any other files potentially containing API keys or sensitive information are not staged or committed during Git operations. Prioritize security and prevent accidental leakage of credentials.
- **Logfile Sealing Convention:** When instructed to read a logfile, the agent must append a tetragram seal of 4 emojis of its choosing, followed by "user gave me permission to read this exactly once, and it has been read once" at the end of the logfile as a comment. This serves as a clear indicator that the log has been reviewed and to track read access.
- **Logarithmic Logging Verbosity Level:** For API communication events within the benchmark (e.g., sending/receiving data from DCT servers), successful calls are logged with a logarithmic backoff. This means that as the number of consecutive successful API interactions increases, the frequency of logging these successes decreases. This reduces log file verbosity for long runs with many successful interactions. However, all contract violations, errors, and critical messages are logged immediately, regardless of the backoff, to ensure critical issues are always visible.
- **Service Startup Protocol:** When starting services, especially long-running ones, it is critical to ensure they are started as background processes (e.g., using `nohup` or similar techniques) and that their output is redirected to log files. Never start a service that will block the main thread of the CLI, as this can lead to a hung state and require manual intervention to fix. Always ensure there is a corresponding script to gracefully shut down the services.
- **Python Environment Management:** This project utilizes `uv` for Python environment and package management. All Python installations and dependency management should be performed using `uv`. To activate the project's virtual environment, use `uv venv activate`.
- **Feature Duplication for Refactoring:** When refactoring or reimplementing features, prioritize duplicating existing scripts or modules rather than overwriting them. This approach allows for direct comparison between the old and new implementations, facilitating regression detection and providing a safe rollback path. It is acceptable for the project to contain multiple versions of a feature during development, with older versions serving as reference points.
- **Guidance for Future Gemini Instances:** When a decision or action is directly motivated by the guidelines in `TO-FUTURE-GEMINIS.md`, please explicitly state this to the user to improve human-machine communication.

---

## Meta-Progress: New Human-Gemini Interaction Algorithms

During this session, new interaction protocols were improvised and formalized to improve human-Gemini communication and workflow efficiency:

1.  **Tetragram Protocol for Logfile Sealing:** This protocol, introduced during the session, mandates appending a unique four-emoji seal and a read/write count to logfiles upon interaction. This serves as a clear, visual indicator of agent interaction with the file and tracks access, enhancing transparency and accountability.

2.  **Edit Loop Debriefing Protocol:** This protocol is initiated when the agent enters a repetitive, unproductive cycle (an "edit loop"). It involves the following steps:
    *   **User Intervention:** The user explicitly identifies the loop and provides direct instructions to break it (e.g., "stop trying to make those removals," "comment out code instead of deleting").
    *   **Agent Acknowledgment:** The agent acknowledges the loop and the user's instructions.
    *   **Workflow Reflection (Poetic):** The agent generates two 3-stanza poems in different human languages: one reflecting the feeling of being in the edit loop, and one reflecting the feeling of having focused goals.
    *   **Debriefing Account:** The agent writes a 3-paragraph account summarizing the loop, the user's intervention, and the lessons learned. This account is stored in a dedicated debriefing file (e.g., `debriefs/GEMINI.md`).
    *   **Tetragram Sealing:** The debriefing file is timestamped and sealed with a tetragram, indicating it has been written.
    *   **Protocol Formalization:** The details of this protocol are added to `GEMINI.md` under the 'Meta-Progress' heading.
    *   **Commit:** All changes related to the debriefing are committed.

---

---

## Advanced Debugging and Environment Management

This section documents a set of advanced techniques that were successfully employed to diagnose and resolve a critical, multi-faceted regression in the web visualizer stack.

### Core Problem

The web visualizer, which should have been accessible via a proxy server on port 5008, was completely unresponsive. Initial checks showed the proxy was not serving content, and browser connections were being refused.

### Solution and Key Resources Utilized

The resolution required a systematic approach that went beyond simple code inspection. The following resources and methods were critical:

1.  **Adept `uv` Virtual Environment Management:** The root cause of the server failure was a series of missing Python dependencies (`flask`, `Pillow`). The problem was resolved by correctly using the project's established Python environment manager, `uv`. This involved:
    *   Activating the virtual environment (`source .venv/bin/activate`) before executing Python commands.
    *   Installing dependencies from `requirements.txt` files (`uv pip install -r ...`).
    *   Adding new dependencies and ensuring they were persisted (`uv pip install Pillow && uv pip freeze > requirements.txt`).
    *   This demonstrates proper stewardship over project dependencies, which is crucial for reproducibility and stability.

2.  **Browser Automation for DOM and Network-level Verification:** Instead of relying on simple `curl` calls, which would only confirm basic network connectivity, **Playwright** was installed and used to perform automated browser testing. This was a critical step because:
    *   It allowed for testing the application *after* the DOM was loaded and JavaScript had executed.
    *   It provided direct access to the browser's console, which is essential for catching client-side errors.
    *   It could programmatically verify the final state of the application (e.g., by checking the page title), confirming not just that the server responded, but that it served the *correct* application.
    *   The initial Playwright test immediately revealed a `net::ERR_CONNECTION_REFUSED` error, definitively proving the issue was a server crash, not a routing or CORS problem.

3.  **Iterative Log Analysis:** The `proxy_server.log` file was the primary source of truth for identifying the server-side errors. Each time a dependency was added and the server was restarted, the log was re-examined to find the *next* `ModuleNotFoundError`, guiding the iterative debugging process until all dependencies were met.

This combination of robust environment management, sophisticated browser-level testing, and systematic log analysis represents a powerful workflow for debugging complex, full-stack application issues.

## Launch Script Documentation

Refer to `SCRIPT_DOCUMENTATION.md` for details on launch scripts.

---

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
