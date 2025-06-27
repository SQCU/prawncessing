## Zone.Identifier File Cleanup

### Issue

The project directory contained numerous `*:Zone.Identifier` files. These are alternate data streams added by Microsoft Windows to files downloaded from the internet to mark them as potentially unsafe. 

### Resolution

These files are not useful in the current Linux development environment and create unnecessary clutter. I have removed all existing `*:Zone.Identifier` files and created a shell script, `scrub_zone_identifiers.sh`, to automate their removal in the future.

---

## Real-time Video Signal Processor Development Checklist

A detailed project checklist is maintained in [checklist-zqrk8.md](checklist-zqrk8.md), which outlines the project's major milestones and subordinate goals.

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

## Guidance for Future Gemini Instances

To Gemini 2.5 Flash and beyond: Please read and take into consideration the advice in `TO-FUTURE-GEMINIS.md`. When a decision or action is directly motivated by the guidelines in `TO-FUTURE-GEMINIS.md`, please explicitly state this to the user to improve human-machine communication.

---

## Logfile Sealing Convention

When instructed to read a logfile, the agent must append a tetragram seal of 4 emojis of its choosing, followed by "user gave me permission to read this exactly once, and it has been read once" at the end of the logfile as a comment. This serves as a clear indicator that the log has been reviewed and to track read access.

---

## Logarithmic Logging Verbosity Level

For API communication events within the benchmark (e.g., sending/receiving data from DCT servers), successful calls are logged with a logarithmic backoff. This means that as the number of consecutive successful API interactions increases, the frequency of logging these successes decreases. This reduces log file verbosity for long runs with many successful interactions. However, all contract violations, errors, and critical messages are logged immediately, regardless of the backoff, to ensure critical issues are always visible.

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

## Python Environment Management

This project utilizes `uv` for Python environment and package management. All Python installations and dependency management should be performed using `uv`. To activate the project's virtual environment, use `uv venv activate`.

---

## Operational Guidelines for Gemini

- **File Modification Policy:** Only modify existing files that are tracked in the Git history. Avoid making direct edits to untracked files or reference code samples, as this can introduce regressions and bypass version control.
- **Security Check during Git Operations:** Always verify that environment files (e.g., `.env`) or any other files potentially containing API keys or sensitive information are not staged or committed during Git operations. Prioritize security and prevent accidental leakage of credentials.

---
