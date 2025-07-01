# Architectural Blueprint: The Decoupled Real-time Service

This document outlines a robust and modular architecture for building Python services that need to return results to a real-time interface, like a web browser dataview. The core philosophy is to decouple the business logic from the web interface, enabling high reusability, testability, and scalability.

## Core Philosophy

The architecture is built on a layered approach with a central communication bus. This explicitly separates the "thinking" (core logic) from the "talking" (web interface).

1.  **Modular:** The web part doesn't know *how* the work is done.
2.  **Reusable:** Core logic can be used by any interface (REST, WebSocket, CLI) without modification.
3.  **Scalable:** The system can handle many concurrent jobs and connections via a message bus.
4.  **Testable:** Each layer can be unit-tested in isolation.

## Project Structure

```
your_project/
├── core_logic/
│   ├── __init__.py
│   └── processing.py       # Layer 0: Your atomic, stateless functions
├── services/
│   ├── __init__.py
│   └── analysis_runner.py  # Layer 1: Orchestrates calls to core_logic
├── api/
│   ├── __init__.py
│   └── endpoints.py        # Layer 3: The web-facing part (FastAPI with REST/WebSockets)
├── main.py                 # Assembles and runs the FastAPI app
└── requirements.txt        # The project dependencies
```

---

## The Layers: Implementation Details

### `requirements.txt`

These are the necessary libraries for this pattern. Redis is used as the message bus.

```txt
fastapi
uvicorn[standard]
websockets
redis
```

### Layer 0: The Core (`core_logic/processing.py`)

This contains the pure, atomic, stateless computational units. It has no knowledge of the web, I/O, or where it's being called from. It just transforms data.

```python
# core_logic/processing.py

import time
import random

def heavy_computation_step_one(data: dict) -> dict:
    \"\"\"An atomic, stateless function.\"\"\"
    print("CORE: Running step one...")
    time.sleep(0.5)
    data['step_one_result'] = random.randint(1, 100)
    return data

def heavy_computation_step_two(data: dict) -> dict:
    \"\"\"Another atomic, stateless function.\"\"\"
    print("CORE: Running step two...")
    time.sleep(0.5)
    data['step_two_result'] = "processed"
    return data
```

### Layer 1: The Service (`services/analysis_runner.py`)

This layer orchestrates the atomic functions from Layer 0 to perform a complete task. It still knows nothing about the web. Its ability to report progress is provided via **Dependency Injection**—we pass it a `publish` function that it can call with updates.

```python
# services/analysis_runner.py

from typing import Callable, Any, Dict
from core_logic import processing
import json

async def run_full_analysis(
    job_id: str,
    initial_data: Dict,
    publish: Callable[[str, str], Any]
):
    \"\"\"
    Orchestrates the core logic and publishes updates via the provided callback.
    This is the "hot run loop".
    \"\"\"
    current_data = initial_data.copy()
    
    # Announce the start
    await publish(job_id, json.dumps({"status": "started", "progress": 0}))
    
    # Step 1
    current_data = processing.heavy_computation_step_one(current_data)
    update_1 = {"status": "running", "progress": 50, "intermediate_result": current_data}
    await publish(job_id, json.dumps(update_1))
    
    # Step 2
    current_data = processing.heavy_computation_step_two(current_data)
    update_2 = {"status": "complete", "progress": 100, "final_result": current_data}
    await publish(job_id, json.dumps(update_2))

    print(f"SERVICE: Job {job_id} finished.")
```

### Layer 2: The Communication Bus (Redis Pub/Sub)

For a real-time system, we need to decouple the task initiator from the result receiver. Redis Pub/Sub is the canonical solution.

*   **`PUBLISH`**: The background worker publishes updates to a specific channel (e.g., `job_results:job_123`).
*   **`SUBSCRIBE`**: The client's WebSocket handler listens to that same channel for messages.

This "bus" is implemented within the API layer but represents a distinct architectural component.

### Layer 3: The Interface (`api/endpoints.py`)

This is the thin web layer. Its only jobs are to handle HTTP/WebSocket protocols, validate inputs, and delegate tasks to the service layer. It provides the concrete `redis_publisher` function that the service layer requires.

```python
# api/endpoints.py

import asyncio
import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, BackgroundTasks, WebSocketDisconnect

from services.analysis_runner import run_full_analysis

router = APIRouter()
redis_client = redis.from_url("redis://localhost", decode_responses=True)

# This is our concrete publisher function that the service layer will use.
async def redis_publisher(channel: str, message: str):
    \"\"\"Publishes a message to a Redis channel.\"\"\"
    await redis_client.publish(channel, message)

# --- REST Endpoint to START a job ---
@router.post("/analysis/{job_id}")
async def start_analysis(job_id: str, background_tasks: BackgroundTasks):
    \"\"\"
    Non-blocking endpoint to kick off a long-running job.
    \"\"\"
    # BackgroundTasks runs the job without blocking the HTTP response.
    # We inject the job_id and the redis_publisher function into our service.
    background_tasks.add_task(
        run_full_analysis,
        job_id=job_id,
        initial_data={"input": "some_value"},
        publish=redis_publisher
    )
    return {"message": "Analysis started", "job_id": job_id}

# --- WebSocket Endpoint to VIEW the results ---
@router.websocket("/ws/analysis/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    \"\"\"
    Connects a client to listen for results for a specific job_id.
    \"\"\"
    await websocket.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(job_id)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                await websocket.send_text(message['data'])
                if '"status": "complete"' in message['data']:
                    break
            # Heartbeat to check if the client is still connected
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        print(f"WS client for {job_id} disconnected.")
    except Exception as e:
        print(f"WS Error for {job_id}: {e}")
    finally:
        print(f"WS: Unsubscribing and closing for {job_id}")
        await pubsub.unsubscribe(job_id)
        if websocket.client_state.name != 'DISCONNECTED':
            await websocket.close()
```

### Assembling the Application (`main.py`)

This file ties the API router into the main FastAPI application.

```python
# main.py

from fastapi import FastAPI
from api import endpoints

app = FastAPI(title="Real-time Analysis Service")

app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the modular real-time service. See /docs for API."}

# To run: uvicorn main:app --reload
```

## How to Run the Service

1.  **Install dependencies**:
    `pip install -r requirements.txt`

2.  **Run Redis**: Make sure you have a Redis server running. The easiest way is with Docker:
    `docker run -d -p 6379:6379 redis`

3.  **Run the FastAPI app**:
    `uvicorn main:app --reload`

4.  **Interact with the service**:
    a. Open your browser to `http://127.0.0.1:8000/docs` for the API interface.
    b. Use a tool like `curl` or the `/docs` page to start a job. E.g., `curl -X POST http://127.0.0.1:8000/analysis/job123`.
    c. Use a WebSocket client (like a simple HTML/JS page or a command-line tool) to connect to `ws://127.0.0.1:8000/ws/analysis/job123` to see the real-time results.

## Solving the "Ensemble of Servicemaps" Problem

This architecture directly addresses the challenge of reusing "semantically identical" code across multiple backend services.

1.  **Shared Internal Library**: Your `core_logic` and `services` directories can be packaged as an internal Python library. All your different microservices would simply `pip install` this shared, versioned library.

2.  **Service-Specific Interfaces**: Each distinct "servicemap" in your ensemble becomes a new, thin FastAPI project that imports the shared library.
    *   **Service A** might use standard REST calls and WebSockets as defined here.
    *   **Service B** might need to be triggered by a Kafka message. Its entrypoint would be a Kafka consumer that calls `run_full_analysis`, passing in a `kafka_publisher` function.
    *   **Service C** might need different authentication. You simply add FastAPI `Depends()` to its `api/endpoints.py` without ever touching the core logic.

You achieve maximum code reuse by isolating the pure logic (`core_logic`, `services`) from the I/O and protocol-specific details (`api`, `main`).

