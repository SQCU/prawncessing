// worker.js - Dedicated script for parallel block matching.

// --- DCT/IDCT Math Library (Copied here for self-containment) ---
function dct1d(data){const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++)r+=data[c]*Math.cos((2*c+1)*o*t);c[o]=(0===o?Math.sqrt(1/N):Math.sqrt(2/N))*r}return c}function idct1d(data){const N=data.length,c=new Float32Array(N),t=Math.PI/(2*N);for(let o=0;o<N;o++){let r=0;for(let c=0;c<N;c++){r+=(0===c?Math.sqrt(1/N):Math.sqrt(2/N))*data[c]*Math.cos((2*o+1)*c*t)}c[o]=r}return c}function dct2d(data){const N=data.length,c=Array(N).fill(0).map(()=>new Float32Array(N)),t=Array(N).fill(0).map(()=>new Float32Array(N));for(let o=0;o<N;o++)c[o]=dct1d(data[o]);for(let o=0;o<N;o++){const r=c.map(data=>data[o]),d=dct1d(r);for(let c=0;c<N;c++)t[c][o]=d[c]}return t}

// The core search function executed by the worker.
function findBestMatchesInSlice(targetCoeffs, refCoeffsSlice, k) {
    const blockSize = targetCoeffs.length;
    let matches = [];
    for (const ref of refCoeffsSlice) {
        let sad = 0;
        for (let j = 0; j < blockSize; j++) {
            for (let i = 0; i < blockSize; i++) {
                sad += Math.abs(targetCoeffs[j][i] - ref.coeffs[j][i]);
            }
        }
        matches.push({ score: sad, x: ref.x, y: ref.y, coeffs: ref.coeffs });
    }
    matches.sort((a, b) => a.score - b.score);
    return matches.slice(0, k);
}

// Listen for messages from the main thread.
self.onmessage = function(e) {
    const { targetCoeffs, refCoeffsSlice, k } = e.data;
    const bestMatches = findBestMatchesInSlice(targetCoeffs, refCoeffsSlice, k);
    self.postMessage(bestMatches);
};