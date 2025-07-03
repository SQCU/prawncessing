import time
from services.worker_service import WorkerService

class TileSelectionService(WorkerService):
    def __init__(self, name="TileSelectionService", input_type="dct_coefficients", output_type="tile_coordinates"):
        super().__init__(name, "tile_selector", input_type, output_type)

    def process_job(self, job_data):
        try:
            # Placeholder for actual tile selection logic
            print(f"[{self.name}] Selecting tiles for input: {job_data.get('input_data', 'No input')}")
            time.sleep(0.1) # Simulate work
            return b"tile_coordinates_data"
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[{self.name}] Error during job processing: {error_detail}")
            return {"status": "error", "message": str(e), "detail": error_detail}

    def _job_server(self):
        """Listens for jobs from peers and puts them in the queue or handles them directly."""
        while self.running:
            try:
                job_data = self.server_socket.recv_json()
                if job_data.get("task") == "process":
                    response_data = self.process_job(job_data)
                    self.server_socket.send(response_data)
                else:
                    self.server_socket.send_json({"status": "error", "message": "unknown task"})
            except Exception as e:
                print(f"[{self.name}] Job server error: {e}")
