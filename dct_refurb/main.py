

import time
from multiprocessing import Process
import os
import sys
from services.service_mapper import ServiceMapper
from services.worker_service import WorkerService
from services.downscale_service import DownscaleService
from services.dct_processor_service import DCTProcessorService
from services.tile_selection_service import TileSelectionService
from services.diff_smash_service import DiffSmashService

def run_worker(name, service_type, input_type=None, output_type=None):
    """Target function for worker processes."""
    if service_type == "downscaler":
        worker = DownscaleService(name, input_type, output_type)
    elif service_type == "dct_processor":
        worker = DCTProcessorService(name, input_type, output_type)
    elif service_type == "tile_selector":
        worker = TileSelectionService(name, input_type, output_type)
    elif service_type == "diff_smasher":
        worker = DiffSmashService(name, input_type, output_type)
    else:
        worker = WorkerService(name, service_type, input_type, output_type)
    worker.run()

def run_mapper():
    """Target function for the mapper process."""
    mapper = ServiceMapper()
    mapper.run()

def run_web_server():
    """Target function for the web server process."""
    # We import uvicorn here to avoid it being a dependency for the workers
    import uvicorn
    # The app is now in api.web_server
    from api.web_server import app as web_app
    uvicorn.run(web_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # --- Service Execution Safeguard ---
    # This script is designed to be run as a background service.
    # Running it directly in a terminal is not recommended as it will block the session.
    #
    # Recommended execution (from the project root directory):
    #
    # 1. Activate the virtual environment:
    #    source .venv/bin/activate
    #
    # 2. Run the service in the background with output redirected to a log file:
    #    nohup python -u -m dct_refurb.main > dct_refurb/service.log 2>&1 &
    #
    # 3. To monitor the service:
    #    tail -f dct_refurb/service.log
    #
    # 4. To stop the services, you will need to manually kill the processes.
    #    You can find the PIDs in the log file and use:
    #    kill <mapper_pid> <worker_pid_1> <worker_pid_2> ...
    #
    if os.isatty(sys.stdout.fileno()):
        print("="*80)
        print("WARNING: You are running a background service architecture directly in a terminal.")
        print("This is not the intended use case and will block your terminal session.")
        print("Please run this script as a background process. See documentation in main.py.")
        print("="*80)
        time.sleep(5)

    # 1. Start the Service Mapper in its own process
    mapper_proc = Process(target=run_mapper, daemon=True)
    mapper_proc.start()
    time.sleep(1) # Give it a moment to bind

    # 2. Start Worker Services
    # We'll designate Worker-A as our primary image generator
    worker_names = ["Worker-A", "Worker-B"]
    worker_procs = []
    # We'll designate Worker-A as our primary image generator
    worker_configs = [
        {"name": "Worker-A", "service_type": "image_generator", "input_type": "json", "output_type": "image/jpeg"},
        {"name": "Worker-B", "service_type": "image_generator", "input_type": "json", "output_type": "image/jpeg"},
        {"name": "Downscaler-1", "service_type": "downscaler", "input_type": "image/jpeg", "output_type": "image/jpeg"},
        {"name": "DCTProcessor-1", "service_type": "dct_processor", "input_type": "image/jpeg", "output_type": "dct_coefficients"},
        {"name": "TileSelector-1", "service_type": "tile_selector", "input_type": "dct_coefficients", "output_type": "tile_coordinates"},
        {"name": "DiffSmasher-1", "service_type": "diff_smasher", "input_type": "dct_coefficients", "output_type": "image/jpeg"}
    ]
    worker_procs = []
    for config in worker_configs:
        proc = Process(target=run_worker, args=(config["name"], config["service_type"], config["input_type"], config["output_type"]), daemon=True)
        worker_procs.append(proc)
        proc.start()
    
    time.sleep(2) # Give them time to register

    # 3. Start the Web Server
    web_proc = Process(target=run_web_server, daemon=True)
    web_proc.start()

    print("\n--- All services started. Watching workers... ---\n")
    
    # Let the workers run
    try:
        # Keep the main process alive to manage the children
        for proc in worker_procs + [mapper_proc, web_proc]:
            proc.join()
    except KeyboardInterrupt:
        print("\n--- Shutting down all processes ---")
        mapper_proc.terminate()
        for proc in worker_procs:
            proc.terminate()
        web_proc.terminate()


