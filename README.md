# Prawncessing Project

This project focuses on real-time video signal processing, particularly utilizing Discrete Cosine Transform (DCT) for operations like datamoshing. It includes various server implementations (Python/SciPy, Python/NumPy) and an orchestration script for benchmarking.

## Project Structure Overview

*   `.venv/`: Python virtual environment.
*   `orchestrate_benchmark.py`: Script for orchestrating benchmark runs.
*   `benchmark_dct.py`: The core benchmarking script.
*   `scipy_dct_server.py`: DCT server implemented using SciPy.
*   `numpy_dct_server.py`: DCT server implemented using NumPy.
*   `videostream_mock_server.py`: Mock server for video stream input.
*   `GEMINI.md`: Notes and context for Gemini agents.
*   `TO-FUTURE-GEMINIS.md`: Guidance for future Gemini agents.

## Orchestration Script (`orchestrate_benchmark.py`) Control Flow

This diagram illustrates the high-level flow of the `orchestrate_benchmark.py` script, which sets up the necessary servers and runs the DCT benchmark.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                 orchestrate_benchmark.py Control Flow                     │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Initialize: server_processes_info, ascii_stream_process, ports_to_check   │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Clean Ports (3000, 8001, 8002, 8003)                                      │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Start SciPy DCT Server (Port 8001)                                        │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Start NumPy DCT Server (Port 8002)                                        │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Start Videostream Mock Server (Port 8003)                                 │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Wait for all Servers to be Ready (SciPy, NumPy, Videostream Mock)         │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Run API Contract Tests (api_contract_tester.py)                           │
│ (Aborts if tests fail)                                                    │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Print "Starting benchmark..."                                             │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Start benchmark_dct.py as a subprocess                                    │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Read and Display Benchmark Output with tqdm                               │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Wait for benchmark_dct.py to finish                                       │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Print "Benchmark finished."                                               │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ Handle Exceptions (KeyboardInterrupt, RuntimeError)                       │
│ Finally Block: Terminate all started server processes                     │
└───────────┬───────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ End Orchestration Script                                                  │
└───────────────────────────────────────────────────────────────────────────┘
```

## Getting Started

To activate the Python virtual environment:

```bash
source .venv/bin/activate
```

Further instructions for running specific components or tests can be found within the respective script files or by examining `package.json` for available npm scripts.
