# Statement of Intent - 2025-06-29

This document outlines the reasoning for the upcoming test run and provides a preemptive analysis of potential failure modes, as requested.

## Why I Believe the Test Will Succeed

The previous test failures have been characterized by `ConnectionRefusedError` and timeouts. This strongly indicates that the tests were being executed before the background services had fully initialized and bound to their respective ports. This is a classic race condition.

My proposed solution directly addresses this root cause by introducing a dedicated Python script, `wait_for_services.py`. This script will be executed after the services are launched but before the tests are run. It will actively and repeatedly attempt to establish a socket connection to each required port (5000, 5001, 5009, 5010). The test suite will only proceed once this script confirms that all services are listening, thereby eliminating the race condition in a robust way that does not rely on an arbitrary `sleep` period.

Furthermore, a separate bug was identified in `test_visualizer_framerate.py` where it was relying on a non-existent `base_url` configuration. This has been corrected to use the explicit URL `http://localhost:5000`.

By resolving both the primary race condition and the specific test configuration error, I am confident that the test suite will now pass.

## Preemptive Explanation for Potential Non-Termination

If the test suite still fails to terminate (i.e., it hangs and is killed by the 60-second `pytest` timeout), the problem is almost certainly not a failure to *start* the services, but a deadlock *within* one of the services after it has started.

Here is the likely sequence of events in a non-termination scenario:
1.  The `start_services.sh` script successfully launches the Python service processes.
2.  The new `wait_for_services.py` script successfully connects to each port, confirming the services are listening. The script exits with success code 0.
3.  The `pytest` suite begins. A test (e.g., `test_api_contracts.py`) sends a request to a service (e.g., the `echo_service` on port 5010).
4.  The service accepts the connection but enters an infinite loop or a blocking state while processing the request. It never sends a response.
5.  The test, waiting for a response, hangs until the `pytest --timeout=60` limit is reached and the test runner is terminated.

In this scenario, the `pre-kill` script (`kill_ports.sh`) has already done its job by ensuring no old processes are interfering. The failure would therefore be a runtime bug in the service application logic itself, not an environment or test setup issue.


## Update

The test run subsequent to this statement failed in the exact same manner as previous attempts. The test script became non-terminating and required manual user intervention to halt. The 'active polling' solution in 'wait_for_services.py' did not resolve the underlying issue causing the services or tests to hang.
