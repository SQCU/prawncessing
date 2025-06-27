# Script Documentation

### `start_visualizer_services.sh`
*Last Updated: 2025-06-27*

This script orchestrates the launch of visualizer-related services. It first kills existing processes on relevant ports (5007 for visualizer, 8003 for mock video stream, 5008 for proxy) and then starts the `videostream_mock_server.py` and `proxy_server.py` in the background using `nohup`. The `proxy_server.py` now also serves the `visualizer.html` and `visualizer.js` files. Their output is redirected to `videostream_mock_server.log` and `proxy_server.log` respectively.

*   **To run:** `./start_visualizer_services.sh`
*   **To access visualizer:** Navigate your browser to `http://localhost:5008/visualizer.html`
*   **To stop:** Use `./kill_ports.sh 5007 8003 5008` or manually kill processes on these ports.

### `proxy_server.py`
*Last Updated: 2025-06-27*

This Flask application acts as a reverse proxy, forwarding requests from the visualizer clients to the appropriate backend services. It runs on port 5008 and handles CORS issues by adding `Access-Control-Allow-Origin: *` headers to all responses. It also serves static files like `visualizer.html` and `visualizer.js` from the project root directory.

*   **To run:** Launched by `start_visualizer_services.sh`. Can be run independently via `python3 proxy_server.py`.
*   **To stop:** Part of `start_visualizer_services.sh`'s cleanup, or manually kill the process on port 5008.

### `functional_processor/start_functional_processors.sh`
*Last Updated: 2025-06-27*

This script starts all individual functional processor services (DCT, Reference Frame, Difference, Accumulator, Orchestration) in the background using `nohup`. This ensures they continue to run even if the terminal session is closed. Their output is redirected to `.log` files in their respective directories (e.g., `logs/dct_service.log`).

*   **To run:** `./functional_processor/start_functional_processors.sh`
*   **To stop:** Manually kill processes on ports 5002-5006 or use a dedicated stop script if available.
