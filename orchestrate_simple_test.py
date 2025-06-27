

import subprocess
import time
import os
import signal
from server_utils import start_server, terminate_processes, clean_ports, wait_for_videostream_ready

if __name__ == "__main__":
    server_processes_info = []
    ports_to_check = [3000, 8001, 8002, 8003]

    try:
        clean_ports(ports_to_check)

        # Start JavaScript DCT server
        js_server_command = "node js_dct_server.js"
        server_processes_info.append({'name': "JavaScript DCT", 'command': js_server_command, 'process': start_server(js_server_command, "JavaScript DCT")})

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

        # Add a small initial sleep after starting all servers
        time.sleep(1)

        # Wait for videostream mock server to be ready
        if not wait_for_videostream_ready("http://127.0.0.1:8003"):
            raise RuntimeError("Videostream mock server failed to become ready.")

        print("Starting simple DCT test...")
        test_command = ". .venv/bin/activate && python simple_dct_test.py"
        test_process = subprocess.Popen(test_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Read and display test output
        for line in test_process.stdout:
            print(line, end='')

        test_process.wait()
        print("Simple DCT test finished.")

    except KeyboardInterrupt:
        print("\nOrchestration interrupted.")
    except RuntimeError as e:
        print(f"Orchestration failed: {e}")
    finally:
        terminate_processes(server_processes_info)

