### Session Checklist: Datamoshing Engine Foundation

*   **Success Rubric:** The core DCT, Difference, and Accumulator modules are implemented as standalone, testable services.
*   **Subordinate Goals:**
    *   [x] **DCT Service:**
        *   [x] Implement a functional, standalone DCT service in `functional_processor/dct_service.py`.
        *   [x] Write unit tests to verify the correctness of the forward and inverse DCT operations.
    *   [x] **Difference Service:**
        *   [x] Implement a service in `functional_processor/difference_service.py` that calculates the difference between two DCT data blocks.
        *   [x] Write unit tests to validate the difference calculation.
    *   [x] **Accumulator Service:**
        *   [x] Implement a service in `functional_processor/accumulator_service.py` that can sum DCT difference blocks over time.
        *   [x] Write unit tests for the accumulation logic.
    *   [x] **Reference Frame Manager:**
        *   [x] A module to hold and provide a reference frame for processing.