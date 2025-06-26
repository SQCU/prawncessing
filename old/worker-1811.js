// worker.js - High-performance parallel frame processing engine.

// --- DCT/IDCT Math Library (Unchanged) ---
const dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
const idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};


// --- NEW FEATURE: NORMALIZED CROSS-CORRELATION (NCC) KERNEL ---
/**
 * Calculates the mean and standard deviation of a single 2D coefficient block.
 * This is a helper for the NCC calculation.
 * @param {Float32Array[]} block - A 2D array of DCT coefficients.
 * @returns {{mean: number, stdDev: number}}
 */
function getBlockStats(block) {
    const N = block.length;
    const size = N * N;
    let sum = 0;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) sum += block[j][i];
    const mean = sum / size;
    let sumSqDiff = 0;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) sumSqDiff += (block[j][i] - mean) ** 2;
    const stdDev = Math.sqrt(sumSqDiff / size);
    return { mean, stdDev };
}

/**
 * Computes the Normalized Cross-Correlation between two RGB DCT coefficient blocks.
 * NCC is robust to linear changes in brightness and contrast, measuring structural similarity.
 * A score of 1 indicates a perfect match, -1 a perfect inverse, and 0 no correlation.
 * @param {Array<Float32Array[]>} blockA - The first RGB coefficient block.
 * @param {Array<Float32Array[]>} blockB - The second RGB coefficient block.
 * @returns {number} The average NCC score across the R, G, B channels.
 */
function normalizedCrossCorrelation(blockA, blockB) {
    const N = blockA[0].length;
    let totalNcc = 0;
    
    for (let c = 0; c < 3; c++) { // For each color channel (R, G, B)
        const statsA = getBlockStats(blockA[c]);
        const statsB = getBlockStats(blockB[c]);
        
        // Denominator for the NCC formula
        const denominator = statsA.stdDev * statsB.stdDev;
        if (denominator < 1e-6) { // Avoid division by zero for flat blocks
            totalNcc += (statsA.stdDev < 1e-6 && statsB.stdDev < 1e-6) ? 1.0 : 0.0;
            continue;
        }

        let crossCorrSum = 0;
        for (let j = 0; j < N; j++) {
            for (let i = 0; i < N; i++) {
                crossCorrSum += (blockA[c][j][i] - statsA.mean) * (blockB[c][j][i] - statsB.mean);
            }
        }
        totalNcc += crossCorrSum / (N * N * denominator);
    }
    return totalNcc / 3.0; // Average NCC over the three channels
}


/**
 * Analyzes an input block against all reference blocks using NCC,
 * then normalizes the best score using z-score for content-agnostic thresholding.
 */
function analyzeAndFindBestMatch(targetCoeffs, refCoeffsGrid) {
    const allNccScores = [];
    let bestMatch = { score: -Infinity, coeffs: null, pos: null };

    // 1. Calculate NCC against all reference blocks and find the best match.
    for (const ref of refCoeffsGrid) {
        const ncc = normalizedCrossCorrelation(targetCoeffs, ref.coeffs);
        allNccScores.push(ncc);
        if (ncc > bestMatch.score) {
            bestMatch = { score: ncc, coeffs: ref.coeffs, pos: ref.pos };
        }
    }
    
    // 2. Calculate mean and standard deviation of all NCC scores.
    const n = allNccScores.length;
    if (n === 0) return { bestMatch, normalizedScore: 0, allNccScores: [] };
    const mean = allNccScores.reduce((a, b) => a + b, 0) / n;
    const stdDev = Math.sqrt(allNccScores.map(x => (x - mean) ** 2).reduce((a, b) => a + b, 0) / n);

    // 3. Normalize the best score (z-score). A higher score is better.
    // We reverse the z-score formula slightly since higher NCC is better (unlike SAD where lower is better).
    const normalizedScore = stdDev > 0 ? (bestMatch.score - mean) / stdDev : 0;

    return { bestMatch, normalizedScore, allScores: allNccScores };
}

// --- UTILITY FUNCTIONS (Unchanged) ---
function extractRGBBlock(imageData, x, y, blockSize, width) { const block = [Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))]; for(let j=0; j<blockSize; j++) for(let i=0; i<blockSize; i++) { const idx = ((y+j)*width+(x+i))*4; block[0][j][i]=imageData[idx]-128; block[1][j][i]=imageData[idx+1]-128; block[2][j][i]=imageData[idx+2]-128; } return block; }
function computeRGBDCT(rgbBlock) { return [ dct2d(rgbBlock[0]), dct2d(rgbBlock[1]), dct2d(rgbBlock[2]) ]; }
function reconstructRGBBlock(coeffs) { return [ idct2d(coeffs[0]), idct2d(coeffs[1]), idct2d(coeffs[2]) ]; }

self.onmessage = (e) => {
    try {
        const { procW, procH, blockSize, nValue, similarityThreshold, inputSlice, refCoeffsGrid } = e.data;
        const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
        const decisionPlan = []; // The "plan" for visualization on the main thread
        const allFrameScores = []; // All z-scores for this worker's slice

        for (let gy = 0; gy * blockSize < procH; gy++) {
            for (let gx = 0; gx * blockSize < procW; gx++) {
                const y = gy * blockSize;
                const x = gx * blockSize;
                
                const blockIMG = extractRGBBlock(inputSlice.data, x, y - (Math.floor(y/procH) * procH), blockSize, procW);
                const coeffsIMG = computeRGBDCT(blockIMG);
                const { bestMatch, normalizedScore, allScores } = analyzeAndFindBestMatch(coeffsIMG, refCoeffsGrid);
                allFrameScores.push(normalizedScore);

                if (!bestMatch || !bestMatch.coeffs) continue;
                
                let coeffsRECON;
                let blockDecision;

                // Higher normalizedScore is a better match.
                if (normalizedScore > similarityThreshold) {
                    blockDecision = 'interpolate';
                    coeffsRECON = [Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))];
                    for(let c=0; c<3; c++) for(let j=0; j<blockSize; j++) for(let i=0; i<blockSize; i++) coeffsRECON[c][j][i] = (1 - nValue) * coeffsIMG[c][j][i] + nValue * bestMatch.coeffs[c][j][i];
                } else {
                    blockDecision = 'passthrough';
                    coeffsRECON = coeffsIMG;
                }

                // Add this block's outcome to the decision plan for the main thread.
                decisionPlan.push({ gx, gy, blockDecision, refPos: bestMatch.pos });

                const reconstructed = reconstructRGBBlock(coeffsRECON);
                for (let j=0; j<blockSize; j++) for (let i=0; i<blockSize; i++) {
                    const canvasIdx = ((y+j)*procW+(x+i))*4;
                    outputPixels[canvasIdx]   = Math.max(0, Math.min(255, reconstructed[0][j][i] + 128));
                    outputPixels[canvasIdx+1] = Math.max(0, Math.min(255, reconstructed[1][j][i] + 128));
                    outputPixels[canvasIdx+2] = Math.max(0, Math.min(255, reconstructed[2][j][i] + 128));
                    outputPixels[canvasIdx+3] = 255;
                }
            }
        }
        
        self.postMessage({ 
            outputPixels,       // For the 'Summer Output' panel
            decisionPlan,       // For the 'Search Similarity' and 'Top Tiles' panels
            frameStats: { scores: allFrameScores } // For the adaptive EMA range
        });

    } catch (error) {
        console.error("Error in worker:", error);
        self.postMessage(null);
    }
};