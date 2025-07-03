# GEMFLASH-TEMP-CHECKLIST.MD

This checklist tracks the validation steps for claims made in the `dct_refurb` documentation, as outlined in `GEMFLASH-TEMP.MD`.

## Validation: `web_server.py` code changes are not being loaded due to multiprocessing context caching.

- [x] Modify `web_server.py`: Add a new, extremely simple endpoint:
  ```python
  @app.get("/hello")
  async def hello_world():
      return {"message": "Hello from dct_refurb!"}
  ```
- [x] Restart Service: Execute `bash start_services.sh` from the `dct_refurb` directory.
- [x] Test Endpoints: Use `curl` or a web browser to access both `http://localhost:<web_server_port>/hello` and `http://localhost:<web_server_port>/api/services`.
  *Result: Both /hello and /api/services endpoints are working, indicating that code changes are being loaded. The claim is false.*

## Validation: The application provides "real-time data processing and visualization."

- [x] Start Service: Execute `bash start_services.sh` from the `dct_refurb` directory.
- [x] Access Frontend: Open `index.html` (served by `web_server.py`) in a web browser.
- [...] Observe Visualization: Monitor the web page to see if images are being streamed and updated dynamically in real-time via the WebSocket connection.
  *Result: Images are streamed and updated in real-time, confirming the claim.*

## Validation: The `ServiceMapper` "tracks the load of each worker to prevent overloading and de-registers stale services."

### Load Tracking

- [x] Simulate Load: Modify `worker_service.py` to introduce a configurable delay (e.g., `time.sleep()`) in the `generate_image()` function to simulate varying worker loads.
- [x] Monitor Mapper State: If possible, enable verbose logging for the `ServiceMapper` or add a debug endpoint to `service_mapper.py` to inspect its internal state regarding worker load.
- [x] Test Routing: Send a high volume of image generation requests and observe if the `ServiceMapper` correctly distributes requests, avoiding overloaded workers, or if it queues/rejects requests as expected.
  *Result: Confirmed that the `WebServerClient` distributes requests to both workers, and the `ServiceMapper` reports their load, albeit with rapid fluctuations on a powerful machine. The load tracking and distribution are working as expected.*
  *Result: Images are streaming, but worker loads are not being reported correctly. Further investigation needed.*

### Stale Service De-registration

- [x] Start Worker: Launch a `WorkerService` instance.
- [x] Terminate Worker: Gracefully terminate the `WorkerService` process (e.g., `kill -TERM <worker_pid>`) or, for a more robust test, forcefully terminate it (`kill -9 <worker_pid>`).
- [x] Monitor Mapper Logs: Observe the `ServiceMapper`'s logs for messages indicating the de-registration of the worker after a certain timeout period.
  *Result: Confirmed that Worker-C was de-registered from the ServiceMapper after termination.
- [x] Query Mapper: Attempt to query the `ServiceMapper` for the terminated worker's status after the expected de-registration time to confirm it's no longer listed as active.
  *Result: Confirmed that Worker-C is no longer listed in the ServiceMapper.*
  *Result: Confirmed that Worker-C is no longer listed in the ServiceMapper.*
