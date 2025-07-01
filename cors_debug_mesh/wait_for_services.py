import socket
import time
import sys

def wait_for_ports(ports, timeout=20):
    """
    Waits for a list of ports to be open on localhost.

    Args:
        ports (list): A list of integers representing the ports to check.
        timeout (int): The maximum time to wait in seconds.

    Returns:
        bool: True if all ports are open, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        all_open = True
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect(('localhost', port))
                except (ConnectionRefusedError, ConnectionResetError):
                    all_open = False
                    break
        if all_open:
            print("All services are ready.")
            return True
        time.sleep(0.5)
    print(f"Timeout: Not all services were ready within {timeout} seconds.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wait_for_services.py <port1> <port2> ...")
        sys.exit(1)

    ports_to_check = [int(p) for p in sys.argv[1:]]
    if wait_for_ports(ports_to_check):
        sys.exit(0)
    else:
        sys.exit(1)
