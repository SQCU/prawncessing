
import zmq
import json
import time
import os
import threading
from multiprocessing import Queue

from core_logic.image_generation import generate_image

class WorkerService:
    def __init__(self, name, service_type, input_type=None, output_type=None, mapper_address="tcp://127.0.0.1:5588"):
        self.service_type = service_type
        self.input_type = input_type
        self.output_type = output_type
        self.name = name
        self.pid = os.getpid()
        self.mapper_address = mapper_address
        self.job_queue = Queue(maxsize=10) # Max 10 jobs in queue
        self.active_tasks = 0 # Counter for active image generation tasks

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
            "payload": {
                "name": self.name,
                "address": self.server_address,
                "pid": self.pid,
                "service_type": self.service_type,
                "input_type": self.input_type,
                "output_type": self.output_type
            }
        }
        self.mapper_socket.send_json(payload)
        self.mapper_socket.recv_json() # Wait for ack
        print(f"[{self.name}] Registered with mapper.")

    def _health_reporter(self):
        """Periodically reports queue load to the mapper."""
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
        """Listens for jobs from peers and puts them in the queue or handles them directly."""
        while self.running:
            try:
                job_data = self.server_socket.recv_json()

                if job_data.get("task") == "request_image":
                    # Handle image requests directly and send back the data
                    self.active_tasks += 1
                    print(f"[{self.name}] Starting image generation. Active tasks: {self.active_tasks}")
                    try:
                        image_data = generate_image(self.name)
                        self.server_socket.send(image_data)
                    except Exception as e:
                        print(f"[{self.name}] Error during image generation: {e}")
                    finally:
                        self.active_tasks -= 1
                        print(f"[{self.name}] Finished image generation. Active tasks: {self.active_tasks}")
                    continue

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
        """Main entry point for the worker process."""
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

    def send_job_to_peer(self, peer_name, job_data, load_threshold=0.9, return_response=False):
        """Discovers a peer and sends it a job if not overloaded."""
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
        
        if return_response:
            peer_response = peer_socket.recv()
        else:
            peer_response = peer_socket.recv_json()
            
        peer_socket.close()
        
        if not return_response:
            print(f"[{self.name}] Peer {peer_name} response: {peer_response}")
            return peer_response['status'] == 'ok'
        
        return peer_response

    def list_peers(self):
        """Requests a list of all peers from the mapper."""
        try:
            req_socket = self.context.socket(zmq.REQ)
            req_socket.connect(self.mapper_address)
            req_socket.send_json({"command": "LIST_PEERS", "payload": {}})
            response = req_socket.recv_json()
            req_socket.close()
            return response
        except Exception as e:
            print(f"[{self.name}] Could not list peers: {e}")
            return {"status": "error", "message": str(e)}
