// --- Worker Initialization: Load libraries from local files ---
try {
    importScripts('kdtree.js');
} catch (e) {
    console.error("Worker failed to import kdtree.js", e);
    self.postMessage({ status: 'error', message: 'Could not load kdtree.js' });
    throw e;
}

// --- Worker State ---
let kdTree = null;
let refCoeffsGrid = null;

// --- DCT/IDCT and other helper functions as before ---
const dct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c};
const idct1d=(data)=>{const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c};
const dct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
const idct2d=(data)=>{const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=idct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=idct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t};
function getBlockStats(block) { const N=block.length;const size=N*N;let sum=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++)sum+=block[j][i];const mean=sum/size;let sumSqDiff=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++)sumSqDiff+=(block[j][i]-mean)**2;const stdDev=Math.sqrt(sumSqDiff/size);return{mean,stdDev};}
function normalizedCrossCorrelation(blockA,blockB){const N=blockA[0].length;let totalNcc=0;for(let c=0;c<3;c++){const statsA=getBlockStats(blockA[c]);const statsB=getBlockStats(blockB[c]);const denominator=statsA.stdDev*statsB.stdDev;if(denominator<1e-6){totalNcc+=(statsA.stdDev<1e-6&&statsB.stdDev<1e-6)?1:0;continue;}let crossCorrSum=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++){crossCorrSum+=(blockA[c][j][i]-statsA.mean)*(blockB[c][j][i]-statsB.mean);}totalNcc+=crossCorrSum/(N*N*denominator);}return totalNcc/3;}
function extractRGBBlock(imageData,x,y,blockSize,width){const block=[Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)),Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)),Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))];for(let j=0;j<blockSize;j++)for(let i=0;i<blockSize;i++){const idx=((y+j)*width+(x+i))*4;block[0][j][i]=imageData[idx]-128;block[1][j][i]=imageData[idx+1]-128;block[2][j][i]=imageData[idx+2]-128;}return block;}
function computeRGBDCT(rgbBlock){return[dct2d(rgbBlock[0]),dct2d(rgbBlock[1]),dct2d(rgbBlock[2])];}
function reconstructRGBBlock(coeffs){return[idct2d(coeffs[0]),idct2d(coeffs[1]),idct2d(coeffs[2])];}
function flattenCoeffs(coeffs,bs){const dim=bs*bs*3;const flat=new Float32Array(dim);let k=0;for(let c=0;c<3;c++)for(let j=0;j<bs;j++)for(let i=0;i<bs;i++)flat[k++]=coeffs[c][j][i];return flat;}

// --- Main Message Handler ---
self.onmessage = (e) => {
    const { operation } = e.data;

    if (operation === 'init_tree') {
        const distance = (a, b) => { let d=0; for(let i=0;i<a.length;i++) d+=(a[i]-b[i])**2; return Math.sqrt(d); };
        kdTree = new self.kdTree([], distance, ['flat']);
        kdTree.root = e.data.kdTreeJSON.root;
        refCoeffsGrid = e.data.refCoeffsGrid;
        return;
    }

    if (operation === 'process_slice') {
        if (!kdTree || !refCoeffsGrid) { return; }

        const { procW, procH, blockSize, nValue, similarityThreshold, startRow, inputSlice } = e.data;
        const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
        const decisionPlan = [];
        const allFrameScores = [];

        for (let y = 0; y < procH; y += blockSize) {
            for (let x = 0; x < procW; x += blockSize) {
                const blockIMG = extractRGBBlock(inputSlice.data, x, y, blockSize, procW);
                const coeffsIMG = computeRGBDCT(blockIMG);
                
                const flatIMG = flattenCoeffs(coeffsIMG, blockSize);
                const candidates = kdTree.nearest({ flat: flatIMG }, 5);

                let bestMatch = { score: -Infinity, coeffs: null, pos: null };
                const candidateScores = [];
                for (const [candidatePoint] of candidates) {
                    const refBlockData = refCoeffsGrid.find(b => b.pos.x === candidatePoint.pos.x && b.pos.y === candidatePoint.pos.y);
                    if (!refBlockData) continue;
                    const ncc = normalizedCrossCorrelation(coeffsIMG, refBlockData.coeffs);
                    candidateScores.push(ncc);
                    if (ncc > bestMatch.score) {
                        bestMatch = { score: ncc, coeffs: refBlockData.coeffs, pos: refBlockData.pos };
                    }
                }
                if(candidateScores.length === 0) continue;
                
                const mean = candidateScores.reduce((a, b) => a + b, 0) / candidateScores.length;
                const stdDev = Math.sqrt(candidateScores.map(s => (s-mean)**2).reduce((a,b)=>a+b,0)/candidateScores.length);
                const normalizedScore = stdDev > 1e-6 ? (bestMatch.score - mean) / stdDev : 0;
                allFrameScores.push(normalizedScore);
                
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

// --- HANDSHAKE: Signal that the worker is ready ---
self.postMessage({ status: 'ready' });