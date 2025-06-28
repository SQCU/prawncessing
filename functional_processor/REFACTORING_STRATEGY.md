# Refactoring Strategy: functional_processor

**Objective:** Adopt the robust proxy and browser-testing patterns from the `cors_debug_mesh` project to improve the reliability and testability of the `functional_processor`.

## Key Steps:

1.  **Unify Dependencies:** Consolidate `requirements.txt` to include `flask`, `flask-cors`, `playwright`, and `pytest` to support the new architecture and testing methodology.

2.  **Implement Proxy Router:** Refactor `proxy_server.py` into a simple Flask-based router. This will centralize the entry point for all services (`dct`, `accumulator`, etc.), resolving potential CORS issues and simplifying the client-side interface.

3.  **Add Browser Integration Test:** Create `test_browser_integration.py` using Playwright. This test will provide end-to-end validation by navigating to the proxy's URL and asserting that the application loads correctly.

4.  **Orchestrate Services:** Update `start_functional_processors.sh` to launch all backend services and the refactored proxy. Implement a corresponding `kill_ports.sh` script to ensure a clean state for testing and development.

5.  **Validate:** The primary success metric is the successful execution of the new browser integration test, which will confirm the entire stack is working as intended.
