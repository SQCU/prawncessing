
import zmq
import json
import time

class ServiceMapper:
    def __init__(self, host="127.0.0.1", port=5588):
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
                "service_type": payload.get("service_type"),
                "input_type": payload.get("input_type"),
                "output_type": payload.get("output_type"),
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
        """Removes services that haven't checked in recently."""
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
