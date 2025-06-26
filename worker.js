// worker.js

try {
    importScripts('dct.js', 'kdtree.js');
} catch (e) {
    console.error("Worker failed to import libraries", e);
    self.postMessage({ status: 'error', message: 'Could not load libraries' });
    throw e;
}

let treeInstance = null;
let refCoeffsGrid = null;

function getBlockStats(block) { const N=block.length;const size=N*N;let sum=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++)sum+=block[j][i];const mean=sum/size;let sumSqDiff=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++)sumSqDiff+=(block[j][i]-mean)**2;const stdDev=Math.sqrt(sumSqDiff/size);return{mean,stdDev};}
function normalizedCrossCorrelation(blockA,blockB){const N=blockA[0].length;let totalNcc=0;for(let c=0;c<3;c++){const statsA=getBlockStats(blockA[c]);const statsB=getBlockStats(blockB[c]);const denominator=statsA.stdDev*statsB.stdDev;if(denominator<1e-6){totalNcc+=(statsA.stdDev<1e-6&&statsB.stdDev<1e-6)?1:0;continue;}let crossCorrSum=0;for(let j=0;j<N;j++)for(let i=0;i<N;i++){crossCorrSum+=(blockA[c][j][i]-statsA.mean)*(blockB[c][j][i]-statsB.mean);}totalNcc+=crossCorrSum/(N*N*denominator);}return totalNcc/3;}
function extractRGBBlock(imageData,x,y,blockSize,width){const block=[Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)),Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)),Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))];for(let j=0;j<blockSize;j++)for(let i=0;i<blockSize;i++){const idx=((y+j)*width+(x+i))*4;block[0][j][i]=imageData[idx]-128;block[1][j][i]=imageData[idx+1]-128;block[2][j][i]=imageData[idx+2]-128;}return block;}
function computeRGBDCT(rgbBlock){return[dct2d(rgbBlock[0]),dct2d(rgbBlock[1]),dct2d(rgbBlock[2])];}
function reconstructRGBBlock(coeffs){return[idct2d(coeffs[0]),idct2d(coeffs[1]),idct2d(coeffs[2])];}
function flattenCoeffs(coeffs,bs){const dim=bs*bs*3;const flat=new Float32Array(dim);let k=0;for(let c=0;c<3;c++)for(let j=0;j<bs;j++)for(let i=0;i<bs;i++)flat[k++]=coeffs[c][j][i];return flat;}

self.onmessage = (e) => {
    const { operation } = e.data;
    if (operation === 'init_tree') {
        const distance = (a, b) => { let d=0; for(let i=0;i<a.length;i++) d+=(a[i]-b[i])**2; return Math.sqrt(d); };
        treeInstance = new kdTree(e.data.points, distance, ['flat']);
        refCoeffsGrid = e.data.refCoeffsGrid;
        return;
    }

    if (operation === 'process_slice') {
        if (!treeInstance || !refCoeffsGrid) { return; }
        const { procW, procH, blockSize, nValue, similarityThreshold, startRow, inputSlice } = e.data;
        const outputPixels = new Uint8ClampedArray(inputSlice.data.length);
        const decisionPlan = []; const allFrameScores = [];

        for (let y = 0; y < procH; y += blockSize) {
            for (let x = 0; x < procW; x += blockSize) {
                const blockIMG = extractRGBBlock(inputSlice.data, x, y, blockSize, procW);
                const coeffsIMG = computeRGBDCT(blockIMG);
                const flatIMG = flattenCoeffs(coeffsIMG, blockSize);
                const candidates = treeInstance.nearest( { flat: flatIMG }, 5);

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

                // FINAL FIX: Add a guard to ensure `bestMatch.coeffs` is not null before trying to interpolate.
                // This makes the condition explicit and prevents the crash.
                if (normalizedScore > similarityThreshold && bestMatch.coeffs !== null) {
                    blockDecision = 'interpolate';
                    coeffsRECON = [Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize)), Array(blockSize).fill(0).map(()=>new Float32Array(blockSize))];
                    for(let c=0; c<3; c++) for(let j=0; j<blockSize; j++) for(let i=0; i<blockSize; i++) {
                        coeffsRECON[c][j][i] = (1 - nValue) * coeffsIMG[c][j][i] + nValue * bestMatch.coeffs[c][j][i];
                    }
                } else {
                    // Fallback case for low similarity OR for any weird edge case where a best match wasn't found.
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
    } else if (operation === 'compute_top_tiles_viz') {
        const { decisions, blockSize, panelSize, topKTiles } = e.data;

        const counts = {};
        decisions.forEach(d => {
            if (d.blockDecision === 'interpolate' && d.refPos) {
                const k = `${d.refPos.x},${d.refPos.y}`;
                counts[k] = (counts[k] || 0) + 1;
            }
        });

        const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

        const offscreen = new OffscreenCanvas(panelSize, panelSize);
        const ctx = offscreen.getContext('2d');
        ctx.fillStyle = 'rgb(50, 50, 50)'; // Match the background color in hotloop.js
        ctx.fillRect(0, 0, panelSize, panelSize);

        const vizTileSize = panelSize / 4; // Assuming 4x4 grid for top tiles

        for (let i = 0; i < Math.min(topKTiles, sorted.length); i++) {
            const [k] = sorted[i];
            const [rx, ry] = k.split(',').map(Number);

            const refBlockData = refCoeffsGrid.find(b => b.pos.x === rx && b.pos.y === ry);
            if (!refBlockData) continue;

            const reconstructed = reconstructRGBBlock(refBlockData.coeffs);

            // Create a temporary ImageData to draw on the OffscreenCanvas
            const imageData = ctx.createImageData(blockSize, blockSize);
            for (let j = 0; j < blockSize; j++) {
                for (let i = 0; i < blockSize; i++) {
                    const idx = (j * blockSize + i) * 4;
                    imageData.data[idx] = Math.max(0, Math.min(255, reconstructed[0][j][i] + 128));
                    imageData.data[idx + 1] = Math.max(0, Math.min(255, reconstructed[1][j][i] + 128));
                    imageData.data[idx + 2] = Math.max(0, Math.min(255, reconstructed[2][j][i] + 128));
                    imageData.data[idx + 3] = 255;
                }
            }

            // Draw the block onto the OffscreenCanvas
            // Need to scale it to vizTileSize
            const tempCanvas = new OffscreenCanvas(blockSize, blockSize);
            const tempCtx = tempCanvas.getContext('2d');
            tempCtx.putImageData(imageData, 0, 0);

            ctx.drawImage(tempCanvas,
                          0, 0, blockSize, blockSize, // Source rectangle
                          (i % 4) * vizTileSize,
                          Math.floor(i / 4) * vizTileSize,
                          vizTileSize,
                          vizTileSize // Destination rectangle
                         );
        }

        const imageBitmap = await createImageBitmap(offscreen);
        self.postMessage({ operation: 'top_tiles_viz_result', imageBitmap }, [imageBitmap]);
        return;
    }
};
self.postMessage({ status: 'ready' });