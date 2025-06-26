
// worker.js - High-performance parallel frame processing engine.
// v2 - Fixed OpenCV function names and block size bug.

try {
    importScripts('https://docs.opencv.org/4.9.0/opencv.js');
} catch (e) {
    console.error("Failed to import opencv.js in worker", e);
}

// --- Naive JS DCT/IDCT Math Library (Unchanged) ---
const js_dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const js_idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const js_dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=js_dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=js_dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t.map(row => new Float32Array(row))};
const js_idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=js_idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=js_idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t.map(row => new Float32Array(row))};

// --- OpenCV DCT/IDCT Wrappers (Corrected) ---
function cvDct2d(data) {
    const N = data.length;
    let src = cv.matFromArray(N, N, cv.CV_32F, [].concat.apply([], data));
    let dst = new cv.Mat();
    cv.DCT(src, dst, 0); // Corrected to cv.DCT
    const result = Array.from({ length: N }, (_, j) => new Float32Array(N));
    for (let j = 0; j < N; j++) { for (let i = 0; i < N; i++) { result[j][i] = dst.floatAt(j, i); } }
    src.delete(); dst.delete();
    return result;
}

function cvIdct2d(data) {
    const N = data.length;
    let src = cv.matFromArray(N, N, cv.CV_32F, [].concat.apply([], data));
    let dst = new cv.Mat();
    cv.IDCT(src, dst, 0); // Corrected to cv.IDCT
    const result = Array.from({ length: N }, (_, j) => new Float32Array(N));
     for (let j = 0; j < N; j++) { for (let i = 0; i < N; i++) { result[j][i] = dst.floatAt(j, i); } }
    src.delete(); dst.delete();
    return result;
}

const DCT_Backends = {
    'js': { 'dct': js_dct2d, 'idct': js_idct2d },
    'opencv': { 'dct': cvDct2d, 'idct': cvIdct2d }
};

// --- Core Logic ---
function findBestMatches(targetCoeffs, refCoeffsGrid, k) {
    // Corrected bug: targetCoeffs is [R,G,B], so length is 3. We need the block's side length.
    const blockSize = targetCoeffs[0].length;
    let matches = [];
    for (const ref of refCoeffsGrid) {
        let sad = 0;
        for (let c=0; c<3; c++) {
            for (let j=0; j<blockSize; j++) {
                for (let i=0; i<blockSize; i++) {
                    sad += Math.abs(targetCoeffs[c][j][i] - ref.coeffs[c][j][i]);
                }
            }
        }
        matches.push({ score: sad, coeffs: ref.coeffs, pos: ref.pos });
    }
    matches.sort((a, b) => a.score - b.score);
    return matches.slice(0, k);
}

function extractRGBBlock(imageData, x, y, blockSize, width) {
    const block = [ Array(blockSize).fill(0).map(() => new Float32Array(blockSize)), Array(blockSize).fill(0).map(() => new Float32Array(blockSize)), Array(blockSize).fill(0).map(() => new Float32Array(blockSize)) ];
    for(let j=0; j<blockSize; j++) {
        for(let i=0; i<blockSize; i++) {
            const idx = ((y + j) * width + (x + i)) * 4;
            block[0][j][i] = imageData[idx] - 128; block[1][j][i] = imageData[idx+1] - 128; block[2][j][i] = imageData[idx+2] - 128;
        }
    }
    return block;
}

// --- Message Handler ---
self.onmessage = (e) => {
    try {
        const { procW, procH, blockSize, kValue, nValue, inputSlice, refCoeffsGrid, operation, dctBackend } = e.data;

        if (operation === 'process_slice') {
            if (dctBackend === 'opencv' && typeof cv === 'undefined') { return; }
            const dct2d = DCT_Backends[dctBackend].dct;
            const idct2d = DCT_Backends[dctBackend].idct;

            const computeRGBDCT = (rgbBlock) => [dct2d(rgbBlock[0]), dct2d(rgbBlock[1]), dct2d(rgbBlock[2])];
            const reconstructRGBBlock = (coeffs) => [idct2d(coeffs[0]), idct2d(coeffs[1]), idct2d(coeffs[2])];

            const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
            const diffPixels = new Uint8ClampedArray(inputSlice.data.length);

            for (let y = 0; y < procH; y += blockSize) {
                for (let x = 0; x < procW; x += blockSize) {
                    const blockIMG = extractRGBBlock(inputSlice.data, x, y, blockSize, procW);
                    const coeffsIMG = computeRGBDCT(blockIMG);
                    const bestMatches = findBestMatches(coeffsIMG, refCoeffsGrid, kValue);
                    if (!bestMatches || bestMatches.length === 0) continue;

                    const bestMatchCoeffs = bestMatches[0].coeffs;
                    const matchScore = bestMatches[0].score;
                    const coeffsRECON = Array.from({length:3}, () => Array(blockSize).fill(0).map(() => new Float32Array(blockSize)));

                    for (let c=0; c<3; c++) {
                        for (let j=0; j<blockSize; j++) {
                            for (let i=0; i<blockSize; i++) {
                                coeffsRECON[c][j][i] = (1 - nValue) * coeffsIMG[c][j][i] + nValue * bestMatchCoeffs[c][j][i];
                            }
                        }
                    }

                    const reconstructed = reconstructRGBBlock(coeffsRECON);
                    const normalizedScore = Math.min(255, matchScore / (blockSize * blockSize * 3));

                    for (let j=0; j<blockSize; j++) {
                        for (let i=0; i<blockSize; i++) {
                            const canvasIdx = ((y + j) * procW + (x + i)) * 4;
                            outputPixels[canvasIdx] = Math.max(0, Math.min(255, reconstructed[0][j][i] + 128));
                            outputPixels[canvasIdx + 1] = Math.max(0, Math.min(255, reconstructed[1][j][i] + 128));
                            outputPixels[canvasIdx + 2] = Math.max(0, Math.min(255, reconstructed[2][j][i] + 128));
                            outputPixels[canvasIdx + 3] = 255;
                            diffPixels[canvasIdx] = diffPixels[canvasIdx + 1] = diffPixels[canvasIdx + 2] = 255 - normalizedScore;
                            diffPixels[canvasIdx + 3] = 255;
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
