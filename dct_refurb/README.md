# DCT Refurbished Service

This directory contains a standalone, refurbished DCT service. It has been updated to be fully autonomous from the root directory, with its own startup and utility scripts.

## Usage

To start the service, run the following command from within this directory:

```bash
bash start_services.sh
```

This will handle the following:
- Stopping any previously running services.
- Installing dependencies from `requirements.txt`.
- Starting the service in the background.
- Logging output to `service.log`.

To stop the service, run:

```bash
bash interrupt_services.sh
```

To kill any processes running on the service's ports, run:

```bash
bash kill_ports.sh <port_number>
```

## Common Errors When Extending REST API Service Meshes

When working with and extending REST API service meshes like this one, several common errors can occur. Understanding these can help with debugging:

*   **`ModuleNotFoundError`**: This is a common Python error that occurs when an import statement cannot find the specified module. In the context of a service mesh, this often happens when a service is moved or run from a different directory, and the Python path is no longer correct. The fix is to ensure that all import paths are relative to the new execution context, or that the project is installed as a package.
*   **`Address already in use`**: This error occurs when a service tries to bind to a port that is already in use by another process. This is common in development when a previous instance of the service did not shut down correctly. The `kill_ports.sh` script is provided to help resolve this issue by terminating the process that is holding the port open.
*   **CORS Errors**: Cross-Origin Resource Sharing (CORS) errors occur when a web browser, for security reasons, prevents a web page from making requests to a different domain than the one that served the page. When developing a web-based UI for a service mesh, you will likely encounter these errors. The fix is to configure the API server to include the correct CORS headers in its responses.
*   **Service Discovery Issues**: In a service mesh, services often need to discover and communicate with each other. If a service is not registered correctly with the service discovery mechanism (in this case, the "mapper" service), other services will not be able to find it. This can lead to a variety of errors, often manifesting as timeouts or connection refused errors.