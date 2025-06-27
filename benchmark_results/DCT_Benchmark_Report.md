# DCT Benchmark Report

This report summarizes the performance benchmark of different DCT implementations.

## Configuration
- Number of frames processed per configuration: 100
- Resolutions tested: [(3840, 1080), (1920, 540), (960, 270), (480, 135)]
- Block sizes tested: [8, 16, 32]

## Raw Results
```json
[]
```

## Visualizations
### Average DCT Time by Resolution
![Average DCT Time by Resolution](benchmark_plots/avg_dct_time_resolution.png)

### Average DCT Time by Block Size
![Average DCT Time by Block Size](benchmark_plots/avg_dct_time_block_size.png)

### Average IDCT Time by Resolution
![Average IDCT Time by Resolution](benchmark_plots/avg_idct_time_resolution.png)

### Average IDCT Time by Block Size
![Average IDCT Time by Block Size](benchmark_plots/avg_idct_time_block_size.png)

### Average Reconstruction Error by Resolution
![Average Reconstruction Error by Resolution](benchmark_plots/avg_reconstruction_error_resolution.png)

### Average Reconstruction Error by Block Size
![Average Reconstruction Error by Block Size](benchmark_plots/avg_reconstruction_error_block_size.png)

