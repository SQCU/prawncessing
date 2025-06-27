### Milestone 1: Build a Functional Datamoshing Engine

*   **Success Rubric:** The datamoshing engine can successfully process a video stream, applying DCT, difference, and accumulation operations as verified by unit and integration tests.
*   **Subordinate Goals:**
    *   [ ] **DCT Module:** Implement forward and inverse DCT operations on image data.
    *   [ ] **Difference Module:** Calculate the difference between the DCT of an input frame and a reference frame.
    *   [ ] **Accumulator Module:** "Summer" module that accumulates DCT differences over time according to a schedule.
    *   [ ] **Reference Frame Manager:** A module to hold and provide a reference frame for processing.

### Milestone 2: Develop a Real-Time Web-Based Visualizer & Data Pipeline

*   **Success Rubric:** The web visualizer can successfully display the processed video stream and send user commands to the backend, with data flowing reliably from the source.
*   **Subordinate Goals:**
    *   [ ] **Stabilize Inter-Service Communication:** Systematically diagnose and resolve the network and CORS issues between the visualizer and the various backend services.
    *   [ ] **Implement Robust Data Flow:** Ensure video data flows correctly and efficiently from the mock server, through the functional processing pipeline, and to the web visualizer.
    *   [ ] **Video Stream Endpoint:** An endpoint that provides the processed video stream to the frontend.
    *   [ ] **Interactive Control Interface:** A UI with controls for pausing, playing, and manipulating the datamoshing process.
    *   [ ] **Command Endpoint:** An endpoint that receives and processes user commands from the visualizer.
    *   [ ] **Multi-View Display:** Implement different views for debugging and observing the process (e.g., input, DCT, difference, accumulator, output).

### Milestone 3: Optimize for Performance

*   **Success Rubric:** The end-to-end system can process video at a sustained 30 frames per second.
*   **Subordinate Goals:**
    *   [ ] **Benchmarking Suite:** A set of benchmarks to measure the performance of each module.
    *   [ ] **Bottleneck Identification & Remediation:** A process for identifying and addressing performance bottlenecks in the system.
    *   [ ] **Parallelization Strategy:** A plan for parallelizing the processing pipeline, potentially using web workers or other techniques.
