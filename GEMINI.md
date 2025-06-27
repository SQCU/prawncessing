## Zone.Identifier File Cleanup

### Issue

The project directory contained numerous `*:Zone.Identifier` files. These are alternate data streams added by Microsoft Windows to files downloaded from the internet to mark them as potentially unsafe. 

### Resolution

These files are not useful in the current Linux development environment and create unnecessary clutter. I have removed all existing `*:Zone.Identifier` files and created a shell script, `scrub_zone_identifiers.sh`, to automate their removal in the future.

---

## Real-time Video Signal Processor Development Checklist

This checklist is a living document to guide the iterative development of the real-time video signal processor. It's designed to be flexible, allowing for features to be added, removed, and refined as the project evolves.

### Core Functionality

*   [ ] **Image Input:** Can the system accept a stream of images (i.e., a video)?
*   [ ] **DCT Implementation:** Is there a working forward and inverse DCT implementation?
*   [ ] **Reference Frame:** Can the system hold and use a reference frame?
*   [ ] **Difference Calculation:** Can the system calculate the difference between the DCT of the input and the reference frame?
*   [ ] **Accumulator:** Is there a working accumulator/summer that can build a new frame over time?
*   [ ] **Output:** Can the system display the processed video stream in real-time?

### Performance & Optimization

*   [ ] **Benchmarking:** Are there basic benchmarks for each processing stage?
*   [ ] **Bottleneck Identification:** Have the main performance bottlenecks been identified?
*   [ ] **Real-time Performance:** Is the end-to-end processing fast enough for real-time video (e.g., >30fps)?
*   [ ] **Parallelization:** Can any parts of the process be parallelized (e.g., using web workers or other techniques)?

### Views & Debugging

*   [ ] **Input View:** Is there a view for the original, unprocessed video stream?
*   [ ] **DCT View:** Is there a view for the DCT coefficients?
*   [ ] **Reference View:** Is there a view for the current reference frame?
*   [ ] **Difference View:** Is there a view for the DCT difference?
*   [ ] **Accumulator View:** Is there a view for the state of the accumulator?
*   [ ] **Output View:** Is there a view for the final, processed video stream?
*   [ ] **Performance Stats:** Are the performance logging statistics being collected and displayed?

### Scheduling & Interaction

*   [ ] **Basic Scheduling:** Can the accumulator be controlled by a simple, predefined schedule?
*   [ ] **Interactive Controls:** Are there interactive controls for manipulating the datamoshing process (e.g., pausing, changing the schedule, etc.)?
*   [ ] **User Feedback:** Is there clear visual feedback for user interactions?

### Extensibility & Refinement

*   [ ] **Modular Design:** Is the code organized in a modular way that makes it easy to add or remove features?
*   [ ] **Code Quality:** Is the code clean, readable, and well-documented?
*   [ ] **Error Handling:** Does the system handle errors gracefully?
*   [ ] **Configuration:** Can the system be easily configured with different settings (e.g., video resolution, DCT block size, etc.)?

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
