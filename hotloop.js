// hotloop.js - The core processing pipeline for the application.

/** Safely updates the innerHTML of a stats card, checking for existence first. */
function updateStat(id, text) {
    const el = document.getElementById(`stats-${id}`);
    if (el) el.innerHTML = text;
}

/** Creates the oscillating, sheared tracer image. */
function createTracerImage(p5, pg) {
    pg.background(0); pg.noStroke();
    const orange = p5.color(255, 165, 0); const teal = p5.color(0, 128, 128);
    const segmentHeight = pg.height / 8;
    for (let i = 0; i < 8; i++) {
        pg.fill(i % 2 === 0 ? orange : teal);
        pg.beginShape();
        if (i % 2 === 0) {
            pg.vertex(0, i * segmentHeight); pg.vertex(pg.width, i * segmentHeight);
            pg.vertex(pg.width, (i + 0.5) * segmentHeight); pg.vertex(0, (i + 1) * segmentHeight);
        } else {
            pg.vertex(0, i * segmentHeight); pg.vertex(pg.width, (i + 0.5) * segmentHeight);
            pg.vertex(pg.width, (i + 1) * segmentHeight); pg.vertex(0, (i + 1) * segmentHeight);
        }
        pg.endShape(p5.CLOSE);
    }
}

/** STAGE 1: Acquire and prepare input and reference sources. */
function acquireInputs(p5, frameData, state, uiControls) {
    const startTime = performance.now();
    if (!state.toggles.inputs) { frameData.timers.inputs = 0; updateStat('inputs', 'Disabled'); return frameData; }
    
    const { PANEL_SIZE } = state.constants;
    const currentScale = uiControls.resolution.value();
    const procW = p5.floor(PANEL_SIZE * currentScale); const procH = p5.floor(PANEL_SIZE * currentScale);
    frameData.procW = procW; frameData.procH = procH;
    
    // FIX: Re-create canvases from scratch if size changes. This is the most robust method.
    if (procW > 0 && (procW !== state.lastProcW || procH !== state.lastProcH)) {
        Object.values(state.canvases).forEach(c => c && c.remove()); // Remove all old canvases
        state.canvases = {
            inputs: p5.createGraphics(procW, procH).parent('panel-inputs'),
            ref: p5.createGraphics(procW, procH).parent('panel-ref'),
            diff: p5.createGraphics(procW, procH).parent('panel-diff'),
            postprocess: p5.createGraphics(procW, procH).parent('panel-postprocess'),
            viz: p5.createGraphics(PANEL_SIZE, PANEL_SIZE).parent('panel-viz') // Fixed size
        };
        state.lastProcW = procW; state.lastProcH = procH; state.needsRefRecompute = true;
    }
    if (!state.canvases.inputs) return frameData;

    state.canvases.inputs.image(state.video, 0, 0, procW, procH);
    
    let source; const mode = uiControls.scheduler.value();
    if(mode==='Previous Frame' && state.canvases.postprocess.width>1) source = state.canvases.postprocess;
    else if(mode==='Manual Keyframe') source = state.manualKeyframe;
    else if(mode==='Tracer') { createTracerImage(p5, state.tracerImage); source = state.tracerImage; }
    else source = state.staticRefImage;
    if(mode!=='Static Image') state.needsRefRecompute = true;
    state.canvases.ref.image(source, 0, 0, procW, procH);
    
    if ((mode === 'Tracer' || uiControls.skewStrength.value() > 0) && state.canvases.ref.width > 1) {
        const shear = Math.sin(p5.TWO_PI*(p5.millis()/1000)/uiControls.oscPeriod.value())*uiControls.skewStrength.value();
        let temp=p5.createGraphics(procW,procH); temp.translate(procW/2,procH/2); temp.shearX(shear);
        temp.image(state.canvases.ref,-procW/2,-procH/2,procW,procH); state.canvases.ref.image(temp,0,0); temp.remove();
    }
    frameData.timers.inputs = performance.now() - startTime;
    updateStat('inputs', `Res: ${procW}x${procH}\nTime: ${frameData.timers.inputs.toFixed(1)}ms`);
    return frameData;
}

/** STAGE 2: Compute Ref Coeffs and build the K-D Tree for ANN search. */
function computeReferenceCoeffs(p5, frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.ref) { frameData.timers.coeffs = 0; updateStat('ref', 'Disabled'); return frameData; }
    
    let status = 'Cached';
    if (state.needsRefRecompute && frameData.procW > 0) {
        status = 'Recomputed';
        const ref = state.canvases.ref; ref.loadPixels();
        const bs = uiControls.blockSize.value();
        state.refCoeffsGrid = []; const points = [];
        const dim = bs * bs * 3;
        const flattenCoeffs = (coeffs) => {
            const flat = new Float32Array(dim); let k = 0;
            for(let c=0;c<3;c++) for(let j=0;j<bs;j++) for(let i=0;i<bs;i++) flat[k++] = coeffs[c][j][i];
            return flat;
        };
        for(let gy=0; gy < p5.floor(ref.height / bs); gy++) for(let gx=0; gx < p5.floor(ref.width / bs); gx++) {
            const block = [Array(bs).fill(0).map(()=>new Float32Array(bs)),Array(bs).fill(0).map(()=>new Float32Array(bs)),Array(bs).fill(0).map(()=>new Float32Array(bs))];
            for(let j=0;j<bs;j++) for(let i=0;i<bs;i++){ const idx=((gy*bs+j)*ref.width+(gx*bs+i))*4; block[0][j][i]=ref.pixels[idx]-128; block[1][j][i]=ref.pixels[idx+1]-128; block[2][j][i]=ref.pixels[idx+2]-128;}
            const coeffs = [dct2d(block[0]), dct2d(block[1]), dct2d(block[2])];
            const point = { pos: {x:gx, y:gy}, flat: flattenCoeffs(coeffs) };
            points.push(point);
            state.refCoeffsGrid.push({pos: {x:gx,y:gy}, coeffs});
        }
        const distance = (a, b) => { let d=0; for(let i=0;i<a.length;i++) d+=(a[i]-b[i])**2; return Math.sqrt(d); };
        const dimensions = ['flat'];
        state.kdTree = new kdTree(points, distance, dimensions);
        workers.forEach(w => w.postMessage({ operation: 'init_tree', kdTreeJSON: state.kdTree.toJSON(), refCoeffsGrid: state.refCoeffsGrid }));
        state.needsRefRecompute = false;
    }
    
    frameData.timers.coeffs = performance.now() - startTime;
    updateStat('ref', `Status: ${status}\nTime: ${frameData.timers.coeffs.toFixed(1)}ms`);
    return frameData;
}

/** STAGE 3: Run the parallel ANN search on web workers. */
async function runParallelSearch(frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.diff || !state.canvases.inputs) { frameData.timers.search = 0; frameData.workerResults = []; updateStat('diff', 'Disabled'); return frameData; }
    
    state.canvases.inputs.loadPixels();
    const { procW, procH } = frameData;
    const promises = workers.map((worker) => new Promise(resolve => {
        const i = workers.indexOf(worker);
        const rowsPerWorker = Math.ceil(procH / workers.length);
        const startRow = i * rowsPerWorker;
        if (startRow >= procH) return resolve(null);
        const endRow = Math.min(startRow + rowsPerWorker, procH);
        const sliceHeight = endRow - startRow;
        const sliceData = state.canvases.inputs.pixels.slice(startRow*procW*4, endRow*procW*4);
        
        const messageHandler = (e) => { worker.removeEventListener('message', messageHandler); resolve(e.data); };
        worker.addEventListener('message', messageHandler);
        
        worker.postMessage({
            operation: 'process_slice', procW, procH:sliceHeight, blockSize:uiControls.blockSize.value(), nValue:uiControls.interpolation.value(),
            similarityThreshold:uiControls.similarityThresh.value(), startRow,
            inputSlice:{data:sliceData,width:procW,height:sliceHeight}
        });
    }));
    frameData.workerResults = await Promise.all(promises);
    frameData.timers.search = performance.now() - startTime;
    updateStat('diff', `Workers: ${workers.length}\nTime: ${frameData.timers.search.toFixed(1)}ms`);
    return frameData;
}

/** STAGE 4: Process and aggregate results from workers. */
function processWorkerResults(frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.postprocess || !frameData.workerResults || !state.canvases.postprocess) { frameData.timers.postprocess = 0; updateStat('postprocess', 'Disabled'); return frameData; }
    
    const allScores = frameData.workerResults.flatMap(r => r && r.frameStats ? r.frameStats.scores : []);
    state.lastFrameDecisions = frameData.workerResults.flatMap(r => r ? r.decisionPlan : []);
    if (allScores.length > 0) {
        const a=uiControls.emaAlpha.value();
        state.emaMin=a*Math.min(...allScores)+(1-a)*state.emaMin;
        state.emaMax=a*Math.max(...allScores)+(1-a)*state.emaMax;
    }
    state.canvases.postprocess.loadPixels();
    frameData.workerResults.forEach((result, i) => {
        if(result&&result.outputPixels){
            const rowsPerWorker = Math.ceil(frameData.procH / workers.length);
            state.canvases.postprocess.pixels.set(result.outputPixels, (i*rowsPerWorker)*frameData.procW*4);
        }
    });
    state.canvases.postprocess.updatePixels();
    frameData.timers.postprocess = performance.now() - startTime;
    updateStat('postprocess', `EMA Min/Max: ${state.emaMin.toFixed(2)}/${state.emaMax.toFixed(2)}\nTime: ${frameData.timers.postprocess.toFixed(1)}ms`);
    return frameData;
}

/** STAGE 5: Update all visualization canvases. */
function updateVisualizations(p5, frameData, state, uiControls) {
    const startTime = performance.now();
    if (!state.toggles.viz) { frameData.timers.viz = 0; updateStat('viz', 'Disabled'); return frameData; }
    
    const bs=uiControls.blockSize.value();
    const { diff, inputs, viz, ref } = state.canvases;
    if(!diff || !inputs || !viz || !ref) return frameData;

    diff.background(0);
    state.lastFrameDecisions.forEach(d => {
        const block=inputs.get(d.gx*bs,d.gy*bs,bs,bs);
        diff.push();
        if(d.blockDecision==='interpolate') diff.tint(255,127); else diff.filter(p5.INVERT);
        diff.image(block,d.gx*bs,d.gy*bs,bs,bs);
        diff.pop();
    });

    const counts={};
    state.lastFrameDecisions.forEach(d=>{if(d.blockDecision==='interpolate' && d.refPos){const k=`${d.refPos.x},${d.refPos.y}`;counts[k]=(counts[k]||0)+1;}});
    const sorted=Object.entries(counts).sort((a,b)=>b[1]-a[1]);
    viz.background(50);
    for(let i=0;i<Math.min(uiControls.topKTiles.value(),sorted.length);i++){
        const[k]=sorted[i];const[rx,ry]=k.split(',').map(Number);
        const tile=ref.get(rx*bs,ry*bs,bs,bs);
        viz.image(tile,(i%4)*(state.constants.PANEL_SIZE/4),p5.floor(i/4)*(state.constants.PANEL_SIZE/4),state.constants.PANEL_SIZE/4,state.constants.PANEL_SIZE/4);
    }
    frameData.timers.viz = performance.now() - startTime;
    updateStat('viz', `Decisions: ${state.lastFrameDecisions.length}\nTime: ${frameData.timers.viz.toFixed(1)}ms`);
    return frameData;
}

/** Main Orchestration Loop */
async function runComputationLoop(p5, state, uiControls, workers) {
    while (true) {
        const loopStartTime = performance.now();
        if (!state.video || state.video.width === 0 || state.isComputing) {
            await new Promise(resolve => setTimeout(resolve, 10)); continue;
        }
        state.isComputing = true;
        let frameData = { timers: {} };
        
        try {
            frameData = acquireInputs(p5, frameData, state, uiControls);
            frameData = computeReferenceCoeffs(p5, frameData, state, uiControls, workers);
            frameData = await runParallelSearch(frameData, state, uiControls, workers);
            frameData = processWorkerResults(frameData, state, uiControls, workers);
            updateVisualizations(p5, frameData, state, uiControls);
        } finally {
            const loopEndTime = performance.now();
            const totalLoopTime = loopEndTime - loopStartTime;
            const sumOfStages = Object.values(frameData.timers).reduce((a, b) => a + b, 0);
            const intraLoopGap = totalLoopTime - sumOfStages;
            const crossLoopGap = state.lastLoopEndTime > 0 ? loopStartTime - state.lastLoopEndTime : 0;
            const intraWarn = intraLoopGap > totalLoopTime*0.01 ? '⚠️' : '';
            const crossWarn = crossLoopGap > state.lastLoopTotalTime*0.01 && state.lastLoopTotalTime > 0 ? '⚠️' : '';
            
            updateStat('global', `Total: ${totalLoopTime.toFixed(1)}ms\n` +
                `Intra-Gap: ${intraLoopGap.toFixed(1)}ms ${intraWarn}\nCross-Gap: ${crossLoopGap.toFixed(1)}ms ${crossWarn}`);

            state.lastLoopEndTime = loopEndTime; state.lastLoopTotalTime = totalLoopTime;
            state.isComputing = false;
        }
    }
}