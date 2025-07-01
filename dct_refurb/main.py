

import time
import random
from multiprocessing import Process
import os
import sys
from service_mapper import ServiceMapper
from worker_service import WorkerService

def run_worker(name):
    """Target function for worker processes."""
    worker = WorkerService(name)
    worker.run()

def run_mapper():
    """Target function for the mapper process."""
    mapper = ServiceMapper()
    mapper.run()

def run_web_server():
    """Target function for the web server process."""
    # We import uvicorn here to avoid it being a dependency for the workers
    import uvicorn
    from web_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

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
    #    nohup python -u dct_refurb/main.py > dct_refurb/service.log 2>&1 &
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
    worker_names = ["Worker-A", "Worker-B"]
    worker_procs = []
    for name in worker_names:
        proc = Process(target=run_worker, args=(name,), daemon=True)
        worker_procs.append(proc)
        proc.start()
    
    time.sleep(2) # Give them time to register

    # 3. Start the Web Server
    web_proc = Process(target=run_web_server, daemon=True)
    web_proc.start()

    # 4. Demonstrate peer-to-peer job sending with backpressure awareness
    # We create a temporary client to orchestrate the test
    print("\n--- Orchestrator starting job dispatch ---")
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

    print("\n--- Orchestrator finished. Watching workers... ---\n")
    
    # Let the workers run for a bit
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Shutting down all processes ---")
        mapper_proc.terminate()
        for proc in worker_procs:
            proc.terminate()
        web_proc.terminate()

