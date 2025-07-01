# Architectural Blueprint: The Decoupled Real-time Service Mesh

This document outlines a robust and modular architecture for building multi-process Python applications that provide real-time data to a web interface. The core philosophy is to decouple the business logic from the network and web layers, enabling high reusability, testability, and scalability. This is achieved using a ZeroMQ-based service mesh for discovery and communication.

## Core Philosophy

The architecture is built on a layered approach with a central service mapper for discovery. This explicitly separates the "thinking" (core logic) from the "talking" (network/web interface).

1.  **Modular:** The web server doesn't know *how* the work is done, only how to request it from the service mesh.
2.  **Reusable:** Core logic can be used by any service within the mesh without modification.
3.  **Scalable:** The system can be scaled by adding more worker processes, and the service mapper prevents overload via backpressure reporting.
4.  **Testable:** Each layer (core logic, services, API) can be unit-tested in isolation.

## Visual Flow

```text
+----------------+      1. REGISTER(name, addr)      +-------------------+
| Worker A       | --------------------------------> |                   |
| (Proc 1)       |      2. UPDATE_HEALTH(load)       |   Service Mapper  |
| owns Queue A   | <-------------------------------- |   (Proc 0)        |
+----------------+      3. GET_PEER(B) -> addr_B, load_B  |                   |
       ^         +-------------------+
       | 4. SEND_JOB
       | (if load_B is OK)
       v
+----------------+
| Worker B       |
| (Proc 2)       |
| owns Queue B   |
+----------------+
```

## Project Structure

```
your_project/
├── core_logic/
│   ├── __init__.py
│   └── image_generation.py # Layer 0: Your atomic, stateless functions
├── services/
│   ├── __init__.py
│   ├── service_mapper.py   # Layer 1: The service discovery control plane
│   └── worker_service.py   # Layer 1: The service that runs core logic
├── api/
│   ├── __init__.py
│   └── web_server.py       # Layer 2: The web-facing part (FastAPI with WebSockets)
├── main.py                 # Assembles and runs all processes
└── requirements.txt        # The project dependencies
```

---

## The Layers: Implementation Details

### `requirements.txt`

These are the necessary libraries for this pattern. ZeroMQ is used for inter-process communication, and FastAPI/Uvicorn for the web layer.

```txt
pyzmq
fastapi
uvicorn[standard]
Pillow
```

### Layer 0: The Core (`core_logic/image_generation.py`)

This contains the pure, atomic, stateless computational units. It has no knowledge of the web, I/O, or where it's being called from. It just transforms data.

```python
# core_logic/image_generation.py
from PIL import Image, ImageDraw, ImageFont
import datetime
import io

def generate_image(worker_name):
    """
    Generates an image with a timestamp and the worker's name.
    """
    img = Image.new('RGB', (400, 300), color='darkslateblue')
    d = ImageDraw.Draw(img)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    font = ImageFont.load_default()
    d.text((10,10), f"Worker [{worker_name}] Stream:\n{now}", fill=(255,255,0), font=font)
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return img_io.read()
```

### Layer 1: The Services (`services/`)

This layer contains the running processes that form the service mesh.

#### `service_mapper.py`
A dedicated process that acts as a registry for all other services. It allows workers to discover each other and provides backpressure information to prevent overloading.

#### `worker_service.py`
A process that performs the actual work. It registers with the `ServiceMapper`, listens for jobs from other peers (like the web server), and executes functions from the `core_logic` layer. It can also be a client to other workers.

### Layer 2: The API (`api/web_server.py`)

This is the thin web layer. Its only jobs are to handle HTTP/WebSocket protocols and act as a client to the service mesh. It uses a `WorkerService` instance to communicate with the other workers.

```python
# api/web_server.py
import asyncio
import base64
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from services.worker_service import WorkerService

app = FastAPI()
service_client = WorkerService(name="WebServerClient")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # ... serves the index.html file ...

@app.websocket("/ws/video")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Request an image from a worker in the mesh
            image_data = await asyncio.to_thread(
                service_client.send_job_to_peer,
                "Worker-A",
                {"task": "request_image"},
                return_response=True
            )
            if image_data:
                # Forward the image to the browser over the WebSocket
                b64_image = base64.b64encode(image_data).decode('utf-8')
                await websocket.send_text(f"data:image/jpeg;base64,{b64_image}")
            await asyncio.sleep(0.1)
    # ... exception handling ...
```

### Assembling the Application (`main.py`)

This file uses `multiprocessing` to launch the `ServiceMapper`, one or more `WorkerService` instances, and the `web_server` in their own dedicated processes.

## Launch and Debug Workflow

The service is designed to be managed by the `start_dct_refurb.sh` script. This script handles stopping old processes, installing dependencies, and launching the service in the background.

### How to Run the Service

1.  **Install dependencies** (handled by the script):
    `source .venv/bin/activate && uv pip install -r dct_refurb/requirements.txt`

2.  **Run the application**:
    `./start_dct_refurb.sh`

3.  **Interact with the service**:
    Open your browser to `http://127.0.0.1:8000` to see the real-time video stream.

### Debugging

The most common issues are related to Python's module path. Because the application is run as a module (`python -m dct_refurb.main`), all imports within the `dct_refurb` package must be absolute from the `dct_refurb` root.

**Example:**
- **Correct:** `from dct_refurb.services.worker_service import WorkerService`
- **Incorrect:** `from services.worker_service import WorkerService`

To debug, inspect the service log file for `ModuleNotFoundError` tracebacks.

1.  **Run the start script**: `./start_dct_refurb.sh`
2.  **Check the logs**: `tail -n 20 dct_refurb/service.log`
3.  If you see an error, correct the import path in the relevant file.
4.  Repeat until the service starts cleanly. The log should show the `Uvicorn running...` message.

## Solving the "Ensemble of Servicemaps" Problem

This architecture directly addresses the challenge of reusing code across multiple backend services.

1.  **Shared Internal Library**: Your `core_logic` and `services` directories can be packaged as an internal Python library. All your different microservices would simply `pip install` this shared, versioned library.

2.  **Service-Specific Interfaces**: Each distinct "servicemap" in your ensemble can be a different worker type.
    *   **ImageWorker** might only run `image_generation` logic.
    *   **ReportWorker** might run a different set of functions from `core_logic` to generate reports.
    *   The `web_server` acts as the single point of contact for the outside world, requesting data from the appropriate workers in the mesh.

You achieve maximum code reuse by isolating the pure logic (`core_logic`) from the service orchestration (`services`) and the web interface (`api`).