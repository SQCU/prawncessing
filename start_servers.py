
import subprocess
import time
import os

def start_server(command, name, cwd=None):
    print(f"Starting {name} server...")
    process = subprocess.Popen(command, cwd=cwd, shell=True, preexec_fn=os.setsid)
    print(f"{name} server started with PID: {process.pid}")
    return process

if __name__ == "__main__":
    processes = []

    # Start JavaScript DCT server
    # Ensure node is installed and dct.js is accessible
    js_server_command = "node js_dct_server.js"
    processes.append(start_server(js_server_command, "JavaScript DCT"))

    # Start SciPy DCT server
    # Assuming uvicorn is installed in the virtual environment
    scipy_server_command = ". .venv/bin/activate && uvicorn scipy_dct_server:app --host 127.0.0.1 --port 8001"
    processes.append(start_server(scipy_server_command, "SciPy DCT"))

    # Start NumPy DCT server
    # Assuming uvicorn is installed in the virtual environment
    numpy_server_command = ". .venv/bin/activate && uvicorn numpy_dct_server:app --host 127.0.0.1 --port 8002"
    processes.append(start_server(numpy_server_command, "NumPy DCT"))

    # Start Videostream Mock server
    videostream_mock_command = ". .venv/bin/activate && uvicorn videostream_mock_server:app --host 127.0.0.1 --port 8003"
    processes.append(start_server(videostream_mock_command, "Videostream Mock"))

    print("All servers started. Press Ctrl+C to stop them.")

    try:
        while True:
            time.sleep(1) # Keep the main script alive
    except KeyboardInterrupt:
        print("\nStopping all servers...")
        for p in processes:
            try:
                os.killpg(os.getpgid(p.pid), 15) # Send SIGTERM to the process group
                p.wait(timeout=5)
            except Exception as e:
                print(f"Error stopping process {p.pid}: {e}")
        print("All servers stopped.")

