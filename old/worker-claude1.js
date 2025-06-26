// worker.js - High-performance parallel frame processing engine.

// --- COMPLETE DCT/IDCT Math Library ---
const dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
const idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};

function findBestMatches(targetCoeffs, refCoeffsGrid, k) {
    const blockSize = targetCoeffs.length;
    let matches = [];
    for (const ref of refCoeffsGrid) {
        let sad = 0;
        for (let j=0; j<blockSize; j++) { 
            for (let i=0; i<blockSize; i++) { 
                for (let c=0; c<3; c++) {
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
    return [
        dct2d(rgbBlock[0]),
        dct2d(rgbBlock[1]), 
        dct2d(rgbBlock[2])
    ];
}

function reconstructRGBBlock(coeffs) {
    return [
        idct2d(coeffs[0]),
        idct2d(coeffs[1]),
        idct2d(coeffs[2])
    ];
}

self.onmessage = (e) => {
    try {
        const { procW, procH, blockSize, kValue, nValue, inputSlice, refCoeffsGrid, operation } = e.data;

        if (operation === 'process_slice') {
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
                    const coeffsRECON = [
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
        
        else if (operation === 'find_matches') {
            const { targetCoeffs, refCoeffsSlice, k } = e.data;
            const matches = findBestMatches(targetCoeffs, refCoeffsSlice, k);
            self.postMessage(matches);
        }
        
    } catch (error) {
        console.error("Error in worker:", error);
        self.postMessage(null);
    }
};