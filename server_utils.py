import subprocess
import time
import os
import signal
import requests
import threading

def start_server(command, name, cwd=None):
    print(f"Starting {name} server...")
    process = subprocess.Popen(command, cwd=cwd, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"{name} server started with PID: {process.pid}")

    def log_output(pipe, log_prefix):
        for line in iter(pipe.readline, b''):
            print(f"[{log_prefix}] {line.decode().strip()}")

    threading.Thread(target=log_output, args=(process.stdout, f"{name}-stdout"), daemon=True).start()
    threading.Thread(target=log_output, args=(process.stderr, f"{name}-stderr"), daemon=True).start()

    return process

def terminate_processes(processes):
    print("\nStopping all servers...")
    for p_info in processes:
        p = p_info['process']
        name = p_info['name']
        command = p_info['command']

        if p.poll() is not None:
            print(f"{name} server (PID: {p.pid}) already stopped.")
            continue

        try:
            if "uvicorn" in command or "python" in command:
                signal_to_send = signal.SIGINT
                signal_name = "SIGINT"
            else:
                signal_to_send = signal.SIGTERM
                signal_name = "SIGTERM"

            print(f"Sending {signal_name} to {name} server (PID: {p.pid})...")
            os.killpg(os.getpgid(p.pid), signal_to_send)
            p.wait(timeout=5)

            if p.poll() is None:
                print(f"{name} server (PID: {p.pid}) did not respond to {signal_name}. Sending SIGKILL...")
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                p.wait(timeout=5)
                if p.poll() is None:
                    print(f"Error: {name} server (PID: {p.pid}) could not be terminated.")
            else:
                print(f"{name} server (PID: {p.pid}) stopped gracefully.")

        except Exception as e:
            print(f"Error stopping {name} server (PID: {p.pid}): {e}")
    print("All servers stopped.")

def clean_ports(ports):
    print("\nPerforming pre-run port cleanup...")
    for port in ports:
        try:
            pids_output = subprocess.check_output(f"lsof -t -i :{port}", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if pids_output:
                pids = pids_output.split()
                print(f"  Found processes on port {port} with PID(s): {', '.join(pids)}. Killing them...")
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                time.sleep(0.5)
            else:
                print(f"  No processes found on port {port}.")
        except subprocess.CalledProcessError:
            print(f"  lsof command failed for port {port}. Ensure lsof is installed.")
        except Exception as e:
            print(f"  Error during port cleanup for {port}: {e}")
    print("Port cleanup complete.")

def wait_for_server_ready(url, timeout=30, interval=0.5, name="server"):
    print(f"Waiting for {name} at {url} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.1)
            response = requests.get(url, timeout=interval)
            if response.status_code == 200:
                print(f"{name} is ready.")
                return True
        except requests.exceptions.ConnectionError:
            pass # Connection refused, server not up yet
        except requests.exceptions.Timeout:
            pass # Request timed out, server might be slow to respond
        except Exception as e:
            print(f"An unexpected error occurred while checking {name} readiness: {e}")
        time.sleep(interval)
    print(f"{name} not ready after {timeout} seconds. Aborting.")
    return False

def wait_for_videostream_ready(url, timeout=30, interval=0.5):
    print(f"Waiting for videostream mock server at {url} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            time.sleep(0.1)
            response = requests.get(f"{url}/ready", timeout=interval)
            if response.status_code == 200 and response.json().get("ready"):
                print("Videostream mock server is ready.")
                return True
        except requests.exceptions.ConnectionError as e:
            print(f"Connection refused by {url}: {e}. Retrying...")
        except requests.exceptions.Timeout as e:
            print(f"Connection to {url} timed out: {e}. Retrying...")
        except Exception as e:
            print(f"An unexpected error occurred while checking {url} readiness: {e}")
        time.sleep(interval)
    print(f"Videestream mock server not ready after {timeout} seconds. Aborting.")
    return False
