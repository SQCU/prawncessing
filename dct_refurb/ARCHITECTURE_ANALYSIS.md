# Architecture Analysis: `dct_refurb` Service Mesh

This document outlines the existing high-level call graph and architectural structure of the `dct_refurb` application based on an analysis of its source code.

## High-Level Call Graph

```
[main.py]
    │
    ├── Process(target=run_mapper)
    │   └── [service_mapper.py:ServiceMapper]
    │       └── run() -> listens for commands (REGISTER, GET_PEER, etc.)
    │
    ├── Process(target=run_worker) * (for each worker)
    │   └── [worker_service.py:WorkerService]
    │       ├── run()
    │       │   ├── _register_with_mapper() -> sends 'REGISTER' to ServiceMapper
    │       │   ├── _health_reporter() (Thread) -> sends 'UPDATE_HEALTH' to ServiceMapper
    │       │   └── _job_server() (Thread) -> listens for jobs from peers
    │       │       └── [image_generation.py:generate_image()]
    │       └── send_job_to_peer()
    │           ├── -> sends 'GET_PEER' to ServiceMapper
    │           └── -> sends job to another WorkerService instance
    │
    └── Process(target=run_web_server)
        └── [web_server.py:FastAPI App]
            └── @websocket_endpoint
                └── [worker_service.py:WorkerService.send_job_to_peer()]
                    ├── -> sends 'GET_PEER' to ServiceMapper
                    └── -> sends 'request_image' job to a WorkerService instance
```

## Architectural Overview

The application is a multi-process service mesh designed for real-time data processing and visualization, following the blueprint laid out in `dct_servicemap_refurbished.md`.

1.  **`main.py`**: The entry point, responsible for orchestrating the entire application. It uses Python's `multiprocessing` to launch the `ServiceMapper`, multiple `WorkerService` instances, and the `web_server` in separate, daemonized processes.

2.  **`services/service_mapper.py`**: This is the central discovery service or "control plane." It runs in its own process and acts as a registry for all other services. Workers register with it, and clients query it to find other workers. It also tracks the load of each worker to prevent overloading and de-registers stale services.

3.  **`services/worker_service.py`**: This is the "workhorse" of the application. Each worker runs in its own process and can perform computations. It registers with the `ServiceMapper`, reports its health via a background thread, and listens for jobs from other peers in another thread. It uses the `core_logic` to perform its tasks. The `web_server` also uses a `WorkerService` instance, but as a client to send jobs into the mesh.

4.  **`core_logic/image_generation.py`**: This is the "business logic" layer. It contains pure, stateless functions that perform the actual computations (in this case, generating a timestamped image). It has no knowledge of the surrounding service architecture.

5.  **`api/web_server.py`**: This is the web-facing API layer, built with FastAPI. It serves the `index.html` frontend and provides a WebSocket endpoint. When a client connects via the WebSocket, the server uses its internal `WorkerService` client to request images from the service mesh and streams them back to the browser in real-time.
