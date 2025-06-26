// worker.js - High-performance parallel frame processing engine.

// Import k-d tree library (will be bundled or loaded via importScripts in a real app)
// For this environment, we assume it's available globally as it's included in the HTML.
if (typeof kdTree === 'undefined') {
    self.importScripts('https://unpkg.com/kdtree-javascript@1.0.3/kdtree.js');
}

// --- DCT/IDCT Math Library (Unchanged) ---
const dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
const idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};

// --- Worker State ---
let kdTree = null;
let refCoeffsGrid = null;

// --- Helper Functions (largely unchanged, but used differently) ---
function getBlockStats(block) { /* ... as before ... */ }
function normalizedCrossCorrelation(blockA, blockB) { /* ... as before ... */ }
function extractRGBBlock(imageData, x, y, blockSize, width) { /* ... as before ... */ }
function computeRGBDCT(rgbBlock) { return [ dct2d(rgbBlock[0]), dct2d(rgbBlock[1]), dct2d(rgbBlock[2]) ]; }
function reconstructRGBBlock(coeffs) { return [ idct2d(coeffs[0]), idct2d(coeffs[1]), idct2d(coeffs[2]) ]; }

/** Flattens a 3-channel DCT coefficient block into a single vector. */
function flattenCoeffs(coeffs, bs) {
    const dim = bs * bs * 3; const flat = new Float32Array(dim); let k = 0;
    for(let c=0;c<3;c++) for(let j=0;j<bs;j++) for(let i=0;i<bs;i++) flat[k++] = coeffs[c][j][i];
    return flat;
};

// --- Main Message Handler ---
self.onmessage = (e) => {
    const { operation } = e.data;

    // --- OPERATION: Initialize worker with the K-D Tree ---
    if (operation === 'init_tree') {
        const distance = (a, b) => { let d=0; for(let i=0;i<a.length;i++) d+=(a[i]-b[i])**2; return Math.sqrt(d); };
        // Re-hydrate the k-d tree from the JSON representation sent by the main thread
        kdTree = new kdTree([], distance, ['flat']);
        kdTree.root = e.data.kdTree.root;
        refCoeffsGrid = e.data.refCoeffsGrid;
        return;
    }

    // --- OPERATION: Process an image slice (Now uses ANN search) ---
    if (operation === 'process_slice') {
        if (!kdTree || !refCoeffsGrid) {
            // Worker hasn't been initialized yet, can't process.
            self.postMessage(null); return;
        }

        const { procW, procH, blockSize, nValue, similarityThreshold, startRow, inputSlice } = e.data;
        const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
        const decisionPlan = [];
        const allFrameScores = [];

        for (let y = 0; y < procH; y += blockSize) {
            for (let x = 0; x < procW; x += blockSize) {
                const blockIMG = extractRGBBlock(inputSlice.data, x, y, blockSize, procW);
                const coeffsIMG = computeRGBDCT(blockIMG);
                
                // --- PERFORMANCE BOTTLENECK SOLVED HERE ---
                // 1. Find a few *likely* candidates using the ultra-fast k-d tree.
                const flatIMG = flattenCoeffs(coeffsIMG, blockSize);
                const candidates = kdTree.nearest({ flat: flatIMG }, 5); // Find 5 nearest neighbors

                // 2. Now, run the expensive NCC *only on these few candidates*.
                let bestMatch = { score: -Infinity, coeffs: null, pos: null };
                const candidateScores = [];
                for (const [candidatePoint, distance] of candidates) {
                    const refBlockData = refCoeffsGrid.find(b => b.pos.x === candidatePoint.pos.x && b.pos.y === candidatePoint.pos.y);
                    const ncc = normalizedCrossCorrelation(coeffsIMG, refBlockData.coeffs);
                    candidateScores.push(ncc);
                    if (ncc > bestMatch.score) {
                        bestMatch = { score: ncc, coeffs: refBlockData.coeffs, pos: refBlockData.pos };
                    }
                }
                
                // 3. Normalize the score based on the distribution of the *candidate* scores.
                const mean = candidateScores.reduce((a, b) => a + b, 0) / candidateScores.length;
                const stdDev = Math.sqrt(candidateScores.map(s => (s-mean)**2).reduce((a,b)=>a+b,0)/candidateScores.length);
                const normalizedScore = stdDev > 0 ? (bestMatch.score - mean) / stdDev : 0;
                allFrameScores.push(normalizedScore);
                
                // Reconstruction logic remains the same
                let coeffsRECON; let blockDecision;
                if (normalizedScore > similarityThreshold) {
                    blockDecision = 'interpolate';
                    coeffsRECON = [Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))];
                    for(let c=0; c<3; c++) for(let j=0; j<blockSize; j++) for(let i=0; i<blockSize; i++) coeffsRECON[c][j][i] = (1 - nValue) * coeffsIMG[c][j][i] + nValue * bestMatch.coeffs[c][j][i];
                } else {
                    blockDecision = 'passthrough';
                    coeffsRECON = coeffsIMG;
                }

                const gx = Math.floor(x / blockSize);
                const absolute_gy = Math.floor((startRow + y) / blockSize);
                decisionPlan.push({ gx, gy: absolute_gy, blockDecision, refPos: bestMatch.pos });

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
        
        self.postMessage({ outputPixels, decisionPlan, frameStats: { scores: allFrameScores } });
    }
};