# Architecture: A ZeroMQ-based Service Mapper for Backpressure-Aware Discovery

This document details an architecture for a `servicemapper` service. Its purpose is to allow independent Python `multiprocessing` services to discover one another and intelligently route transactions based on real-time backpressure feedback, all using the ZeroMQ messaging library.

This pattern is designed for building robust, multi-process applications on a single machine (or across machines with minor changes) without the overhead of a heavy broker, while still gaining the benefits of a centralized control plane for discovery and load awareness.

## Core Concepts

1.  **Service Mapper (Control Plane):** A single, dedicated process that acts as a registry. It does **not** route job data. It only handles metadata:
    *   Which services are alive?
    *   What are their 0MQ addresses?
    *   What is their current load (queue saturation)?

2.  **Worker Service (Data Plane):** A `multiprocessing` process that performs actual work. Each worker has:
    *   An internal, in-memory queue for incoming jobs.
    *   A 0MQ server socket to receive jobs from peers.
    *   A 0MQ client socket to talk to the Service Mapper and other peers.
    *   Logic to periodically report its queue/load status to the Service Mapper.

3.  **Backpressure Propagation:**
    *   A worker experiencing high load (e.g., its queue is 90% full) reports this to the Mapper.
    *   Another worker, before sending a new job, can query the Mapper for the target's status.
    *   If the target is overloaded, the sending worker can choose to wait, route the job elsewhere, or handle the failure gracefully. This prevents services from being overwhelmed.

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

---

## The Implementation

This system consists of three key Python files:
1.  `service_mapper.py`: The control plane.
2.  `worker_service.py`: The data plane class definition.
3.  `main.py`: A launcher to start the mapper and multiple workers.

### `requirements.txt`
```txt
pyzmq
```

### 1. The Service Mapper (`service_mapper.py`)

This is a standalone process that listens for commands on a fixed 0MQ port. It's a simple, single-threaded server that manages a dictionary of service states.

```python
# service_mapper.py
import zmq
import json
import time

class ServiceMapper:
    def __init__(self, host="127.0.0.1", port=5555):
        self.registry = {}
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.bind_addr = f"tcp://{host}:{port}"
        self.socket.bind(self.bind_addr)
        print(f"Service Mapper listening on {self.bind_addr}")

    def run(self):
        while True:
            try:
                message_str = self.socket.recv_string()
                message = json.loads(message_str)
                command = message.get("command")
                
                response = self.handle_command(command, message.get("payload", {}))
                
                self.socket.send_json(response)
                
                self._cleanup_stale_services()

            except Exception as e:
                print(f"Mapper Error: {e}")
                self.socket.send_json({"status": "error", "message": str(e)})

    def handle_command(self, command, payload):
        if command == "REGISTER":
            service_name = payload["name"]
            self.registry[service_name] = {
                "address": payload["address"],
                "pid": payload["pid"],
                "load": 0.0, # Initial load is 0
                "last_seen": time.time()
            }
            print(f"Registered: {service_name} at {payload['address']}")
            return {"status": "ok", "message": f"registered {service_name}"}

        elif command == "UPDATE_HEALTH":
            service_name = payload["name"]
            if service_name in self.registry:
                self.registry[service_name]["load"] = payload["load"]
                self.registry[service_name]["last_seen"] = time.time()
                return {"status": "ok"}
            return {"status": "error", "message": "not found"}

        elif command == "GET_PEER":
            service_name = payload["name"]
            peer_info = self.registry.get(service_name)
            if peer_info:
                return {"status": "ok", "peer": peer_info}
            return {"status": "error", "message": "peer not found"}
        
        elif command == "LIST_PEERS":
             return {"status": "ok", "peers": self.registry}

        else:
            return {"status": "error", "message": "unknown command"}

    def _cleanup_stale_services(self, timeout=30):
        \"\"\"Removes services that haven't checked in recently.\"\"\"
        now = time.time()
        stale_services = [
            name for name, info in self.registry.items() 
            if now - info.get("last_seen", 0) > timeout
        ]
        for name in stale_services:
            print(f"De-registering stale service: {name}")
            del self.registry[name]

if __name__ == "__main__":
    mapper = ServiceMapper()
    mapper.run()

```

### 2. The Worker Service (`worker_service.py`)

This is a class that encapsulates the logic for a single worker process. It manages its own threads for listening for jobs and reporting health.

```python
# worker_service.py
import zmq
import json
import time
import os
import threading
from multiprocessing import Queue

class WorkerService:
    def __init__(self, name, mapper_address="tcp://127.0.0.1:5555"):
        self.name = name
        self.pid = os.getpid()
        self.mapper_address = mapper_address
        self.job_queue = Queue(maxsize=10) # Max 10 jobs in queue

        # ZMQ Context setup
        self.context = zmq.Context.instance()
        
        # Socket to receive jobs from peers
        self.server_socket = self.context.socket(zmq.REP)
        self.server_port = self.server_socket.bind_to_random_port("tcp://127.0.0.1")
        self.server_address = f"tcp://127.0.0.1:{self.server_port}"

        # Socket to talk to the mapper
        self.mapper_socket = self.context.socket(zmq.REQ)
        self.mapper_socket.connect(self.mapper_address)

        self.running = True
        print(f"[{self.name}] Initialized. PID: {self.pid}. Listening on {self.server_address}")

    def _register_with_mapper(self):
        payload = {
            "command": "REGISTER",
            "payload": {"name": self.name, "address": self.server_address, "pid": self.pid}
        }
        self.mapper_socket.send_json(payload)
        self.mapper_socket.recv_json() # Wait for ack
        print(f"[{self.name}] Registered with mapper.")

    def _health_reporter(self):
        \"\"\"Periodically reports queue load to the mapper.\"\"\"
        while self.running:
            try:
                load = self.job_queue.qsize() / self.job_queue._maxsize
                payload = {
                    "command": "UPDATE_HEALTH",
                    "payload": {"name": self.name, "load": load}
                }
                # Use a fresh socket for thread safety in REQ/REP pattern
                health_socket = self.context.socket(zmq.REQ)
                health_socket.connect(self.mapper_address)
                health_socket.send_json(payload)
                health_socket.recv_json()
                health_socket.close()
            except Exception as e:
                print(f"[{self.name}] Health report failed: {e}")
            time.sleep(5)

    def _job_server(self):
        \"\"\"Listens for jobs from peers and puts them in the queue.\"\"\"
        while self.running:
            try:
                job_data = self.server_socket.recv_json()
                if self.job_queue.full():
                    print(f"[{self.name}] Queue full. Rejecting job.")
                    self.server_socket.send_json({"status": "error", "message": "queue full"})
                else:
                    self.job_queue.put(job_data)
                    self.server_socket.send_json({"status": "ok", "message": "job accepted"})
            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM: break # Context terminated
                print(f"[{self.name}] Job server error: {e}")

    def run(self):
        \"\"\"Main entry point for the worker process.\"\"\"
        self._register_with_mapper()

        # Start background threads
        health_thread = threading.Thread(target=self._health_reporter, daemon=True)
        server_thread = threading.Thread(target=self._job_server, daemon=True)
        health_thread.start()
        server_thread.start()
        
        # Main work loop (processing jobs from the queue)
        while self.running:
            try:
                job = self.job_queue.get()
                print(f"[{self.name}] Processing job: {job['task']} for {job['duration']}s. Queue size: {self.job_queue.qsize()}")
                time.sleep(job['duration'])
                print(f"[{self.name}] Finished job: {job['task']}")
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
        self.context.term() # This will unblock socket calls
        print(f"[{self.name}] Shutting down.")

    def send_job_to_peer(self, peer_name, job_data, load_threshold=0.9):
        \"\"\"Discovers a peer and sends it a job if not overloaded.\"\"\"
        print(f"[{self.name}] Attempting to send job to {peer_name}...")
        
        # 1. Discover peer and check its load
        req_socket = self.context.socket(zmq.REQ)
        req_socket.connect(self.mapper_address)
        req_socket.send_json({"command": "GET_PEER", "payload": {"name": peer_name}})
        response = req_socket.recv_json()
        req_socket.close()

        if response['status'] != 'ok':
            print(f"[{self.name}] Could not find peer {peer_name}. Aborting.")
            return False

        peer_info = response['peer']
        if peer_info['load'] >= load_threshold:
            print(f"[{self.name}] Peer {peer_name} is overloaded (load: {peer_info['load']:.2f}). Aborting.")
            return False
            
        # 2. Send the job directly to the peer
        peer_address = peer_info['address']
        peer_socket = self.context.socket(zmq.REQ)
        peer_socket.connect(peer_address)
        
        print(f"[{self.name}] Sending job {job_data['task']} to {peer_name} at {peer_address}")
        peer_socket.send_json(job_data)
        peer_response = peer_socket.recv_json()
        peer_socket.close()
        
        print(f"[{self.name}] Peer {peer_name} response: {peer_response}")
        return peer_response['status'] == 'ok'

```

### 3. The Launcher (`main.py`)

This script starts the Service Mapper and several Worker Services in separate processes, demonstrating the entire system in action.

```python
# main.py
import time
import random
from multiprocessing import Process
from service_mapper import ServiceMapper
from worker_service import WorkerService

def run_worker(name):
    \"\"\"Target function for worker processes.\"\"\"
    worker = WorkerService(name)
    worker.run()

def run_mapper():
    \"\"\"Target function for the mapper process.\"\"\"
    mapper = ServiceMapper()
    mapper.run()

if __name__ == "__main__":
    # 1. Start the Service Mapper in its own process
    mapper_proc = Process(target=run_mapper, daemon=True)
    mapper_proc.start()
    time.sleep(1) # Give it a moment to bind

    # 2. Start Worker Services
    worker_names = ["Worker-A", "Worker-B"]
    worker_procs = []
    for name in worker_names:
        proc = Process(target=run_worker, args=(name,), daemon=True)
        worker_procs.append(proc)
        proc.start()
    
    time.sleep(2) # Give them time to register

    # 3. Demonstrate peer-to-peer job sending with backpressure awareness
    # We create a temporary client to orchestrate the test
    print("\\n--- Orchestrator starting job dispatch ---")
    client_worker = WorkerService("Orchestrator-Client")
    
    # Send a job from Orchestrator to Worker-A
    client_worker.send_job_to_peer(
        "Worker-A", 
        {"task": "process_video", "duration": 4}
    )
    
    # Send another job, this time to Worker-B
    client_worker.send_job_to_peer(
        "Worker-B", 
        {"task": "calculate_report", "duration": 3}
    )
    
    # Try to send a job to Worker-A again, which should still be busy.
    # Its load will be > 0, but hopefully not over the threshold yet.
    client_worker.send_job_to_peer(
        "Worker-A", 
        {"task": "second_video", "duration": 4}
    )

    print("\\n--- Orchestrator finished. Watching workers... ---\\n")
    
    # Let the workers run for a bit
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n--- Shutting down all processes ---")
        mapper_proc.terminate()
        for proc in worker_procs:
            proc.terminate()
```