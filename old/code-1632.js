// worker.js - High-performance parallel frame processing engine.

// --- COMPLETE DCT/IDCT Math Library ---
const dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
const idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};

/**
 * Calculates the Sum of Absolute Differences (SAD) for all reference blocks,
 * finds the best match, and then normalizes its score based on the mean and
 * standard deviation of all calculated scores.
 * @returns {{bestMatch: object, normalizedScore: number}}
 */
function analyzeAndFindBestMatch(targetCoeffs, refCoeffsGrid) {
    const blockSize = targetCoeffs[0].length;
    const scores = [];
    let bestMatch = { score: Infinity, coeffs: null, pos: null };

    // 1. Calculate all scores and find the best raw match simultaneously
    for (const ref of refCoeffsGrid) {
        let sad = 0;
        for (let c = 0; c < 3; c++) {
            for (let j = 0; j < blockSize; j++) {
                for (let i = 0; i < blockSize; i++) {
                    sad += Math.abs(targetCoeffs[c][j][i] - ref.coeffs[c][j][i]);
                }
            }
        }
        scores.push(sad);
        if (sad < bestMatch.score) {
            bestMatch.score = sad;
            bestMatch.coeffs = ref.coeffs;
            bestMatch.pos = ref.pos;
        }
    }
    
    // 2. Calculate mean and standard deviation of all scores
    const n = scores.length;
    if (n === 0) return { bestMatch, normalizedScore: 0 };
    
    const mean = scores.reduce((a, b) => a + b, 0) / n;
    const stdDev = Math.sqrt(scores.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b, 0) / n);

    // 3. Normalize the best score (handle division by zero if all scores are identical)
    const normalizedScore = stdDev > 0 ? (bestMatch.score - mean) / stdDev : 0;

    return { bestMatch, normalizedScore };
}


function extractRGBBlock(imageData, x, y, blockSize, width) {
    const block = [
        Array(blockSize).fill(0).map(() => new Float32Array(blockSize)),
        Array(blockSize).fill(0).map(() => new Float32Array(blockSize)),
        Array(blockSize).fill(0).map(() => new Float32Array(blockSize))
    ];
    for(let j=0; j<blockSize; j++) {
        for(let i=0; i<blockSize; i++) {
            const idx = ((y + j) * width + (x + i)) * 4;
            block[0][j][i] = imageData[idx] - 128;     // R
            block[1][j][i] = imageData[idx+1] - 128;   // G  
            block[2][j][i] = imageData[idx+2] - 128;   // B
        }
    }
    return block;
}

function computeRGBDCT(rgbBlock) {
    return [ dct2d(rgbBlock[0]), dct2d(rgbBlock[1]), dct2d(rgbBlock[2]) ];
}

function reconstructRGBBlock(coeffs) {
    return [ idct2d(coeffs[0]), idct2d(coeffs[1]), idct2d(coeffs[2]) ];
}

self.onmessage = (e) => {
    try {
        const { procW, procH, blockSize, nValue, similarityThreshold, inputSlice, refCoeffsGrid, operation } = e.data;

        if (operation === 'process_slice') {
            const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
            const diffPixels = new Uint8ClampedArray(inputSlice.data.length);

            for (let y = 0; y < procH; y += blockSize) {
                for (let x = 0; x < procW; x += blockSize) {
                    
                    const blockIMG = extractRGBBlock(inputSlice.data, x, y, blockSize, procW);
                    const coeffsIMG = computeRGBDCT(blockIMG);
                    const { bestMatch, normalizedScore } = analyzeAndFindBestMatch(coeffsIMG, refCoeffsGrid);
                    
                    if (!bestMatch || !bestMatch.coeffs) continue;
                    
                    const bestMatchCoeffs = bestMatch.coeffs;
                    let coeffsRECON;

                    // A more negative score is a better match.
                    if (normalizedScore < similarityThreshold) {
                        // GOOD MATCH: Interpolate the block
                        coeffsRECON = [
                            Array(blockSize).fill(0).map(() => new Float32Array(blockSize)),
                            Array(blockSize).fill(0).map(() => new Float32Array(blockSize)),
                            Array(blockSize).fill(0).map(() => new Float32Array(blockSize))
                        ];
                        
                        for (let c=0; c<3; c++) {
                            for (let j=0; j<blockSize; j++) {
                                for (let i=0; i<blockSize; i++) {
                                    coeffsRECON[c][j][i] = (1 - nValue) * coeffsIMG[c][j][i] + nValue * bestMatchCoeffs[c][j][i];
                                }
                            }
                        }
                        
                        // Set DIFF panel to GREEN for modified blocks
                        for (let j=0; j<blockSize; j++) {
                            for (let i=0; i<blockSize; i++) {
                                 const canvasIdx = ((y + j) * procW + (x + i)) * 4;
                                 diffPixels[canvasIdx] = 0;
                                 diffPixels[canvasIdx + 1] = 180; // Darker green
                                 diffPixels[canvasIdx + 2] = 0;
                                 diffPixels[canvasIdx + 3] = 255;
                            }
                        }

                    } else {
                        // POOR MATCH: Passthrough the original block
                        coeffsRECON = coeffsIMG;

                        // Set DIFF panel to RED for unmodified blocks
                        for (let j=0; j<blockSize; j++) {
                            for (let i=0; i<blockSize; i++) {
                                 const canvasIdx = ((y + j) * procW + (x + i)) * 4;
                                 diffPixels[canvasIdx] = 180; // Darker Red
                                 diffPixels[canvasIdx + 1] = 0;
                                 diffPixels[canvasIdx + 2] = 0;
                                 diffPixels[canvasIdx + 3] = 255;
                            }
                        }
                    }

                    const reconstructed = reconstructRGBBlock(coeffsRECON);
                    
                    for (let j=0; j<blockSize; j++) {
                        for (let i=0; i<blockSize; i++) {
                            const canvasIdx = ((y + j) * procW + (x + i)) * 4;
                            outputPixels[canvasIdx] = Math.max(0, Math.min(255, reconstructed[0][j][i] + 128));
                            outputPixels[canvasIdx + 1] = Math.max(0, Math.min(255, reconstructed[1][j][i] + 128));
                            outputPixels[canvasIdx + 2] = Math.max(0, Math.min(255, reconstructed[2][j][i] + 128));
                            outputPixels[canvasIdx + 3] = 255;
                        }
                    }
                }
            }
            self.postMessage({ outputPixels, diffPixels });
        }
        
    } catch (error) {
        console.error("Error in worker:", error);
        self.postMessage(null);
    }
};