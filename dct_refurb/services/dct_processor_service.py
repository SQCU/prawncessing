import time
from services.worker_service import WorkerService

class DCTProcessorService(WorkerService):
    def __init__(self, name="DCTProcessorService", input_type="image/jpeg", output_type="dct_coefficients"):
        super().__init__(name, "dct_processor", input_type, output_type)

    def process_job(self, job_data):
        try:
            # Placeholder for actual DCT and truncation logic
            print(f"[{self.name}] Processing DCT for input: {job_data.get('input_data', 'No input')}")
            time.sleep(0.1) # Simulate work
            return b"dct_coefficients_data"
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
