# ┌───────────────────────────────────────────────────────────────────────────┐
# │                 orchestrate_benchmark.py Control Flow                     │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Initialize: server_processes_info, ascii_stream_process, ports_to_check   │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Clean Ports (3000, 8001, 8002, 8003)                                      │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Start SciPy DCT Server (Port 8001)                                        │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Start NumPy DCT Server (Port 8002)                                        │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Start Videostream Mock Server (Port 8003)                                 │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Wait for all Servers to be Ready (SciPy, NumPy, Videostream Mock)         │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Run API Contract Tests (api_contract_tester.py)                           │
# │ (Aborts if tests fail)                                                    │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Print "Starting benchmark..."                                             │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Start benchmark_dct.py as a subprocess                                    │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Read and Display Benchmark Output with tqdm                               │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Wait for benchmark_dct.py to finish                                       │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Print "Benchmark finished."                                               │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ Handle Exceptions (KeyboardInterrupt, RuntimeError)                       │
# │ Finally Block: Terminate all started server processes                     │
# └───────────┬───────────────────────────────────────────────────────────────┘
#             │
#             ▼
# ┌───────────────────────────────────────────────────────────────────────────┐
# │ End Orchestration Script                                                  │
# └───────────────────────────────────────────────────────────────────────────┘

import subprocess
import time
import os
import signal
from tqdm import tqdm
import requests
import threading
from server_utils import start_server, terminate_processes, clean_ports, wait_for_videostream_ready, wait_for_server_ready

if __name__ == "__main__":
    server_processes_info = []
    ascii_stream_process = None
    ports_to_check = [3000, 8001, 8002, 8003]

    try:
        clean_ports(ports_to_check)

        # Start JavaScript DCT server (DISABLED: Persistent issues, not critical for core goal)
        # js_server_command = "node js_dct_server.js"
        # server_processes_info.append({'name': "JavaScript DCT", 'command': js_server_command, 'process': start_server(js_server_command, "JavaScript DCT")})

        # Start SciPy DCT server
        scipy_server_command = ". .venv/bin/activate && uvicorn scipy_dct_server:app --host 127.0.0.1 --port 8001 --log-level warning --no-access-log"
        server_processes_info.append({'name': "SciPy DCT", 'command': scipy_server_command, 'process': start_server(scipy_server_command, "SciPy DCT")})

        # Start NumPy DCT server
        numpy_server_command = ". .venv/bin/activate && uvicorn numpy_dct_server:app --host 127.0.0.1 --port 8002 --log-level warning --no-access-log"
        server_processes_info.append({'name': "NumPy DCT", 'command': numpy_server_command, 'process': start_server(numpy_server_command, "NumPy DCT")})

        # Start Videostream Mock server
        videostream_mock_command = ". .venv/bin/activate && uvicorn videostream_mock_server:app --host 127.0.0.1 --port 8003 --log-level warning --no-access-log"
        videostream_mock_info = {'name': "Videostream Mock", 'command': videostream_mock_command, 'process': start_server(videostream_mock_command, "Videostream Mock")}
        server_processes_info.append(videostream_mock_info)

        # Wait for all servers to be ready
        # if not wait_for_server_ready("http://127.0.0.1:3000", name="JavaScript DCT"): # DISABLED: Persistent issues, not critical for core goal
        #     raise RuntimeError("JavaScript DCT server failed to become ready.")
        if not wait_for_server_ready("http://127.0.0.1:8001", name="SciPy DCT"):
            raise RuntimeError("SciPy DCT server failed to become ready.")
        if not wait_for_server_ready("http://127.0.0.1:8002", name="NumPy FFT"):
            raise RuntimeError("NumPy FFT server failed to become ready.")
        if not wait_for_videostream_ready("http://127.0.0.1:8003"):
            raise RuntimeError("Videostream mock server failed to become ready.")

        # Start ASCII video stream (temporarily commented out to avoid interference)
        # ascii_stream_command = ". .venv/bin/activate && python ascii_video_stream.py"
        # ascii_stream_process = subprocess.Popen(ascii_stream_command, shell=True, preexec_fn=os.setsid)
        # print(f"ASCII video stream started with PID: {ascii_stream_process.pid}")

        print("Running API contract tests...")
        contract_test_command = ". .venv/bin/activate && python api_contract_tester.py"
        contract_test_process = subprocess.run(contract_test_command, shell=True, capture_output=True, text=True)
        print(contract_test_process.stdout)
        print(contract_test_process.stderr)

        if contract_test_process.returncode != 0:
            raise RuntimeError(f"API contract tests failed with exit code {contract_test_process.returncode}. Aborting benchmark.")
        print("API contract tests passed.")

        print("Starting benchmark...")
        # Changed to run benchmark_dct.py again
        benchmark_command = ". .venv/bin/activate && python benchmark_dct.py"
        benchmark_process = subprocess.Popen(benchmark_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Read and display benchmark output with tqdm
        for line in tqdm(benchmark_process.stdout, desc="Benchmark Progress", unit="line"): 
            print(line, end='')

        benchmark_process.wait()
        print("Benchmark finished.")

    except KeyboardInterrupt:
        print("\nOrchestration interrupted.")
    except RuntimeError as e:
        print(f"Orchestration failed: {e}")
    finally:
        if ascii_stream_process:
            try:
                os.killpg(os.getpgid(ascii_stream_process.pid), signal.SIGTERM)
                ascii_stream_process.wait(timeout=5)
            except Exception as e:
                print(f"Error stopping ASCII stream process: {e}")
        terminate_processes(server_processes_info)