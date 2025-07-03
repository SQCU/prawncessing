# GEMFLASH-TEMP-CHECKLIST: Extending dct_refurb with a Visualizer and Service String Orchestration

This checklist outlines the steps to extend the `dct_refurb` service with a new visualizer page that allows users to "wire together" services into a "service string" for execution.

## Phase 1: New Visualizer Page and Service Map Display

- [x] **1.1 Create new visualizer endpoint:**
    - Added a new route `/visualizer` to `dct_refurb/api/web_server.py` that serves `visualizer.html`.
- [x] **1.2 Create `visualizer.html`:**
    - Created `dct_refurb/visualizer.html` with basic HTML structure and ensured it loads `visualizer.js`.
    - Reverted `dct_refurb/index.html` to its original state.
- [x] **1.3 Display Service Map:**
    - Implemented JavaScript in `visualizer.html` to fetch the current service map from the `ServiceMapper`.
    - Displayed the available services and their input/output types on the page.

## Phase 2: Service Wiring and Service String Generation

- [x] **2.1 Implement drag-and-drop or click-to-connect UI:**
    - Implemented drag-and-drop to place services onto the workflow area.
    - Implemented click-to-connect for wiring services.
- [x] **2.2 Validate connections:**
    - Implemented client-side logic to validate connections based on input/output type compatibility.
- [x] **2.3 Generate "Service String":**
    - Implemented a mechanism to translate the wired workflow into a structured "service string" (JSON) representing the sequence of service calls.

## Phase 3: Service String Endpoint and Execution

- [x] **3.1 Create "Service String" execution endpoint:**
    - Added a new endpoint `/execute_service_string` to `dct_refurb/api/web_server.py` that accepts the generated "service string."
- [x] **3.2 Implement Service String Parser and Executor:**
    - Developed server-side logic to parse the "service string" and dynamically call services in sequence.

## Phase 4: Integration with Datamoshing Algorithm (Conceptual)

- [x] **4.1 Define service interfaces for datamoshing components:**
    - Defined conceptual input/output interfaces for `DownscaleService`, `DCTService`, `TruncateSpectralService`, `TileSelectionService`, `FullResolutionDCTService`, and `DiffSmashService`.
- [x] **4.2 Implement core datamoshing services:**
    - Created placeholder implementations for `DownscaleService`, `DCTProcessorService`, `TileSelectionService`, and `DiffSmashService`.
    - Modified `main.py` to launch these new services.
- [ ] **4.3 Test end-to-end workflow:**
    - Ready for manual testing. User to wire services in visualizer, generate service string, and execute via curl.

## Phase 5: Debugging and Refinements

- [x] **5.1 Debug Missing Services in Visualizer:**
    - Identified that the `visualizer.js` frontend was not correctly parsing the `peers` object from the `/api/services` endpoint.
    - Modified `dct_refurb/static/visualizer.js` to correctly access the `peers` array.
    - Identified and fixed the `Name: undefined` issue by correctly extracting the service name from the object key in `visualizer.js`.
    - **Verification:** User to open `http://localhost:8000/visualizer` and confirm services are displayed with correct names.

---
**Note:** This checklist will be updated as development progresses and new insights are gained.
