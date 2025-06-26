
# P5.js Architecture vs. GEMINI.md Checklist

This document compares the current p5.js project architecture to the development checklist in `GEMINI.md`.

---

## Core Functionality

*   [✅] **Image Input:** The system uses `createCapture(VIDEO)` in `sketch.js` and `hotloop.js` to get a video stream from a webcam.
*   [✅] **DCT Implementation:** `dct.js` provides `dct2d` and `idct2d` functions. These are used in `worker.js` for processing and in the older `sketch.js`.
*   [✅] **Reference Frame:** The system maintains a reference frame. In `hotloop.js`, this is managed through `state.buffers.ref` and can be a static image, the previous frame, or a tracer image. The older `sketch.js` uses a `refBuffer`.
*   [<!>] **Difference Calculation:** This is where the implementation diverges significantly from the diagram. The `sketch.js` file *does* perform a direct DCT subtraction. However, the more advanced `hotloop.js`/`worker.js` implementation calculates "difference" in a more abstract way: it finds the *best matching* block in the reference frame for a given input block using a k-d tree on DCT coefficients and then calculates a normalized cross-correlation score. This score is a measure of similarity, not a direct difference. So, while a "difference" is computed, it's not the one from the diagram.
*   [❌] **Accumulator:** There is no accumulator or "summer" in the sense of the diagram. The system does not build a frame over time by accumulating differences. Instead, it either passes through the original block or interpolates it with the best-matching reference block based on the similarity score. This architectural choice may lead to a perception of "stalled" processing if the user expects a frame to build up over time.
*   [✅] **Output:** The system displays the processed video stream in real-time on an HTML canvas.

## Performance & Optimization

*   [✅] **Benchmarking:** `hotloop.js` has basic performance logging for each stage of the pipeline (`Pipeline.acquireInputs`, `Pipeline.computeReferenceCoeffs`, etc.), which are displayed in the UI.
*   [<!>] **Bottleneck Identification:** While there are timers, there's no explicit bottleneck identification logic. The developer must interpret the timers to identify bottlenecks. The move to web workers in `hotloop.js` suggests that the main processing loop was identified as a bottleneck in the older `sketch.js` implementation. Perceived "stalled" behavior might stem from these bottlenecks or from the inherent complexity of the similarity search.
*   [<!>] **Real-time Performance:** This is subjective and depends on the hardware and settings. The UI provides sliders for resolution and other parameters, which directly impact performance. The system is designed for real-time, but it's not guaranteed. Slow performance can be perceived as a stalled process.
*   [✅] **Parallelization:** `hotloop.js` and `worker.js` use Web Workers to parallelize the search for matching blocks, which is the most computationally intensive part of the process.

## Views & Debugging

*   [✅] **Input View:** The `inputs` buffer in `hotloop.js` holds the current video frame.
*   [❌] **DCT View:** There is no dedicated view for the DCT coefficients.
*   [✅] **Reference View:** The `ref` buffer in `hotloop.js` holds the reference frame.
*   [✅] **Difference View:** The `diff` buffer in `hotloop.js` is used to visualize the decisions made by the worker (inverting or tinting blocks).
*   [❌] **Accumulator View:** Since there is no accumulator, there is no view for it.
*   [✅] **Output View:** The main canvas displays the final processed video stream.
*   [✅] **Performance Stats:** The UI displays performance statistics for each pipeline stage.

## Scheduling & Interaction

*   [<!>] **Basic Scheduling:** The "scheduler" in the UI (`ui.js`) is not a scheduler in the sense of the diagram. It's a mode selector that determines the source of the reference frame ('Previous Frame', 'Manual Keyframe', 'Tracer', 'Static Image'). It doesn't schedule the application of differences over time.
*   [✅] **Interactive Controls:** `ui.js` creates a rich set of interactive controls (sliders, dropdowns, checkboxes) for manipulating the datamoshing process.
*   [✅] **User Feedback:** The UI provides clear visual feedback for user interactions, including updating performance stats and visualizations.

## Extensibility & Refinement

*   [✅] **Modular Design:** The code is reasonably modular. `dct.js`, `kdtree.js`, `hotloop.js`, `ui.js`, and `worker.js` all have distinct responsibilities. The pipeline in `hotloop.js` is broken down into clear stages.
*   [<!>] **Code Quality:** The code is functional but could be improved. There's a mix of coding styles, and some parts are dense and could benefit from more comments and clearer variable names. The use of global variables in `sketch.js` is a sign of a simpler, less robust design.
*   [❌] **Error Handling:** There is very little explicit error handling. For example, the worker import uses a `try...catch` block, but other parts of the code do not handle potential errors gracefully.
*   [✅] **Configuration:** The system is highly configurable through the UI controls, allowing for adjustments to resolution, block size, interpolation, and other parameters.

---

## Stalled / Stuck Signal Processing Elements

Based on the analysis against the `GEMINI.md` checklist, the following elements are identified as either missing, incomplete, or not functioning as originally envisioned, leading to a "stalled" or "stuck" perception in the signal processing pipeline:

*   **Accumulator / Summer Output:** The "Summer Output" consistently shows `Time: 0.0ms` in the UI, confirming that this processing element is stalled or not actively contributing to the output. This aligns with the architectural observation that a true accumulator is missing.
*   [✅] **Top Source Tiles (Refactored):** This visualization was a significant bottleneck, showing processing times in the hundreds to thousands of milliseconds. It has been refactored to offload the computation and rendering to a web worker, which pre-renders the visualization into an `OffscreenCanvas` and transfers it as an `ImageBitmap` to the main thread. This approach significantly improves performance by leveraging parallel processing and efficient data transfer, addressing the previous algorithmic inefficiency.
*   **Difference Calculation (Conceptual Mismatch):** While a "difference" is computed, it's based on similarity (k-d tree search and cross-correlation) rather than a direct DCT subtraction as implied by the diagram. This conceptual mismatch can lead to unexpected processing behavior.
*   **DCT View:** The absence of a dedicated view for DCT coefficients makes it difficult to inspect and verify the output of the DCT processing stage, potentially masking issues or making it seem "stuck" if its internal state cannot be observed.
*   **Accumulator View:** Directly related to the missing accumulator, the lack of a view for it means there's no way to observe the state of a non-existent component.
*   **Basic Scheduling (Limited Scope):** The current "scheduler" primarily controls the reference frame source rather than actively scheduling the application of differences over time. This limits the dynamic control over the datamoshing process.
*   **Error Handling:** The general lack of explicit error handling across the codebase means that issues in any processing stage might fail silently or lead to unexpected behavior without clear diagnostic messages, contributing to a "stuck" perception.
*   **Search Similarity & Reference:** These elements consistently show high processing times (`~270ms` for Search Similarity and `~60ms` for Reference), indicating they are computationally intensive and contribute significantly to the overall processing time, potentially leading to perceived slowdowns.
