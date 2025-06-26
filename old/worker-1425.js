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
        for (let j=0; j<blockSize; j++) { for (let i=0; i<blockSize; i++) { sad += Math.abs(targetCoeffs[j][i] - ref.coeffs[j][i]); } }
        matches.push({ score: sad, coeffs: ref.coeffs });
    }
    matches.sort((a, b) => a.score - b.score);
    return matches.slice(0, k);
}

self.onmessage = (e) => {
    try {
        const {
            procW,
            procH,
            blockSize,
            kValue,
            nValue,
            inputSlice,
            refCoeffsGrid
        } = e.data;

        // THE FIX: Access the .data property of the inputSlice object.
        const outputPixels = new Uint8ClampedArray(inputSlice.data.length);

        for (let y = 0; y < procH; y += blockSize) {
            for (let x = 0; x < inputSlice.width; x += blockSize) {
                
                const blockIMG = Array(blockSize).fill(0).map(() => new Float32Array(blockSize));
                for(let j=0; j<blockSize; j++) {
                    for(let i=0; i<blockSize; i++) {
                        const idx = ((y + j) * inputSlice.width + (x + i)) * 4;
                        blockIMG[j][i] = (0.299 * inputSlice.data[idx] + 0.587 * inputSlice.data[idx+1] + 0.114 * inputSlice.data[idx+2]) - 128;
                    }
                }

                const coeffsIMG = dct2d(blockIMG);
                const bestMatches = findBestMatches(coeffsIMG, refCoeffsGrid, kValue);
                if (!bestMatches || bestMatches.length === 0) continue;
                
                const bestMatchCoeffs = bestMatches[0].coeffs;
                const coeffsRECON = Array(blockSize).fill(0).map(() => new Float32Array(blockSize));
                for (let j=0; j<blockSize; j++) {
                    for (let i=0; i<blockSize; i++) {
                        coeffsRECON[j][i] = (1 - nValue) * coeffsIMG[j][i] + nValue * bestMatchCoeffs[j][i];
                    }
                }

                const reconstructed = idct2d(coeffsRECON);
                for (let j=0; j<blockSize; j++) {
                    for (let i=0; i<blockSize; i++) {
                        const reconVal = reconstructed[j][i] + 128;
                        const canvasIdx = ((y + j) * inputSlice.width + (x + i)) * 4;
                        outputPixels[canvasIdx] = outputPixels[canvasIdx + 1] = outputPixels[canvasIdx + 2] = reconVal;
                        outputPixels[canvasIdx + 3] = 255;
                    }
                }
            }
        }
        self.postMessage(outputPixels);
    } catch (error) {
        console.error("Error in worker:", error);
        self.postMessage(null); // Signal failure
    }
};