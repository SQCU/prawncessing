// hotloop.js - The core processing pipeline for the application.

const Pipeline = {};

function updateStat(id, text) {
    const el = document.getElementById(`stats-${id}`);
    if (el) el.innerHTML = text;
}
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

Pipeline.acquireInputs = function(p5, frameData, state, uiControls) {
    const startTime = performance.now();
    if (!state.toggles.inputs) { updateStat('inputs', 'Disabled'); return frameData; }
    const { PANEL_SIZE } = state.constants;
    const currentScale = uiControls.resolution.value();
    const procW = p5.floor(PANEL_SIZE * currentScale); const procH = p5.floor(PANEL_SIZE * currentScale);
    frameData.procW = procW; frameData.procH = procH;
    if (procW > 0 && (procW !== state.lastProcW || procH !== state.lastProcH)) {
        Object.values(state.buffers).forEach(b => b && b.remove());
        state.buffers = { inputs: p5.createGraphics(procW, procH), ref: p5.createGraphics(procW, procH), diff: p5.createGraphics(procW, procH), postprocess: p5.createGraphics(procW, procH), viz: p5.createGraphics(PANEL_SIZE, PANEL_SIZE) };
        state.lastProcW = procW; state.lastProcH = procH; state.needsRefRecompute = true;
        state.topTilesVizImageBitmap = null; // Initialize the new state variable
    }
    if (!state.buffers.inputs) return frameData;
    state.buffers.inputs.image(state.video, 0, 0, procW, procH);
    let source; const mode = uiControls.scheduler.value();
    if(mode==='Previous Frame' && state.buffers.postprocess.width > 1) source = state.buffers.postprocess;
    else if(mode==='Manual Keyframe') source = state.manualKeyframe;
    else if(mode==='Tracer') { createTracerImage(p5, state.tracerImage); source = state.tracerImage; }
    else source = state.staticRefImage;
    if(mode!=='Static Image') state.needsRefRecompute = true;
    state.buffers.ref.image(source, 0, 0, procW, procH);
    if ((mode === 'Tracer' || uiControls.skewStrength.value() > 0) && state.buffers.ref.width > 1) {
        const shear = Math.sin(p5.TWO_PI*(p5.millis()/1000)/uiControls.oscPeriod.value())*uiControls.skewStrength.value();
        let temp=p5.createGraphics(procW,procH); temp.translate(procW/2,procH/2); temp.shearX(shear);
        temp.image(state.buffers.ref,-procW/2,-procH/2,procW,procH); state.buffers.ref.image(temp,0,0); temp.remove();
    }
    frameData.timers.inputs = performance.now() - startTime;
    updateStat('inputs', `Res: ${procW}x${procH}\nTime: ${frameData.timers.inputs.toFixed(1)}ms`);
    return frameData;
};

Pipeline.computeReferenceCoeffs = function(p5, frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.ref) { updateStat('ref', 'Disabled'); return frameData; }
    let status = 'Cached';
    if (state.needsRefRecompute && frameData.procW > 0 && state.buffers.ref) {
        status = 'Recomputed';
        const ref = state.buffers.ref; ref.loadPixels();
        const bs = uiControls.blockSize.value();
        state.refCoeffsGrid = []; const points = [];
        const dim = bs * bs * 3;
        const flattenCoeffs = (coeffs) => { const flat = new Float32Array(dim); let k = 0; for(let c=0;c<3;c++) for(let j=0;j<bs;j++) for(let i=0;i<bs;i++) flat[k++] = coeffs[c][j][i]; return flat; };
        for(let gy=0; gy < p5.floor(ref.height / bs); gy++) for(let gx=0; gx < p5.floor(ref.width / bs); gx++) {
            const block = [Array(bs).fill(0).map(()=>new Float32Array(bs)),Array(bs).fill(0).map(()=>new Float32Array(bs)),Array(bs).fill(0).map(()=>new Float32Array(bs))];
            for(let j=0;j<bs;j++) for(let i=0;i<bs;i++){ const idx=((gy*bs+j)*ref.width+(gx*bs+i))*4; block[0][j][i]=ref.pixels[idx]-128; block[1][j][i]=ref.pixels[idx+1]-128; block[2][j][i]=ref.pixels[idx+2]-128;}
            const coeffs = [dct2d(block[0]), dct2d(block[1]), dct2d(block[2])];
            const point = { pos: {x:gx, y:gy}, flat: flattenCoeffs(coeffs) };
            points.push(point);
            state.refCoeffsGrid.push({pos: {x:gx,y:gy}, coeffs});
        }
        workers.forEach(w => w.postMessage({ operation: 'init_tree', points: points, refCoeffsGrid: state.refCoeffsGrid }));
        state.needsRefRecompute = false;
    }
    frameData.timers.coeffs = performance.now() - startTime;
    updateStat('ref', `Status: ${status}\nTime: ${frameData.timers.coeffs.toFixed(1)}ms`);
    return frameData;
};

Pipeline.runParallelSearch = async function(frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.diff || !state.buffers.inputs) { updateStat('diff', 'Disabled'); frameData.workerResults = []; return frameData; }
    state.buffers.inputs.loadPixels();
    const { procW, procH } = frameData;
    const promises = workers.map((worker) => new Promise(resolve => {
        const i = workers.indexOf(worker);
        const rowsPerWorker = Math.ceil(procH / workers.length);
        const startRow = i * rowsPerWorker;
        if (startRow >= procH) return resolve(null);
        const endRow = Math.min(startRow + rowsPerWorker, procH);
        const sliceHeight = endRow - startRow;
        const sliceData = state.buffers.inputs.pixels.slice(startRow*procW*4, endRow*procW*4);
        const messageHandler = (e) => { worker.removeEventListener('message', messageHandler); resolve(e.data); };
        worker.addEventListener('message', messageHandler);
        worker.postMessage({ operation: 'process_slice', procW, procH:sliceHeight, blockSize:uiControls.blockSize.value(), nValue:uiControls.interpolation.value(), similarityThreshold:uiControls.similarityThresh.value(), startRow, inputSlice:{data:sliceData,width:procW,height:sliceHeight} });
    }));
    frameData.workerResults = await Promise.all(promises);
    frameData.timers.search = performance.now() - startTime;
    updateStat('diff', `Workers: ${workers.length}\nTime: ${frameData.timers.search.toFixed(1)}ms`);
    return frameData;
};

Pipeline.processWorkerResults = function(frameData, state, uiControls, workers) {
    const startTime = performance.now();
    if (!state.toggles.postprocess || !frameData.workerResults || !state.buffers.postprocess) { updateStat('postprocess', 'Disabled'); return frameData; }
    const allScores = frameData.workerResults.flatMap(r => r && r.frameStats ? r.frameStats.scores : []);
    state.lastFrameDecisions = frameData.workerResults.flatMap(r => r ? r.decisionPlan : []);
    if (allScores.length > 0) {
        const a=uiControls.emaAlpha.value();
        state.emaMin=a*Math.min(...allScores)+(1-a)*state.emaMin;
        state.emaMax=a*Math.max(...allScores)+(1-a)*state.emaMax;
    }
    state.buffers.postprocess.loadPixels();
    frameData.workerResults.forEach((result, i) => {
        if(result&&result.outputPixels){
            const rowsPerWorker = Math.ceil(frameData.procH / workers.length);
            state.buffers.postprocess.pixels.set(result.outputPixels, (i*rowsPerWorker)*frameData.procW*4);
        }
    });
    state.buffers.postprocess.updatePixels();
    frameData.timers.postprocess = performance.now() - startTime;
    updateStat('postprocess', `EMA Min/Max: ${state.emaMin.toFixed(2)}/${state.emaMax.toFixed(2)}\nTime: ${frameData.timers.postprocess.toFixed(1)}ms`);

    // Send message to worker to compute top tiles visualization
    if (workers.length > 0 && state.toggles.viz) {
        workers[0].postMessage({
            operation: 'compute_top_tiles_viz',
            decisions: state.lastFrameDecisions,
            blockSize: uiControls.blockSize.value(),
            panelSize: state.constants.PANEL_SIZE,
            topKTiles: uiControls.topKTiles.value()
        });
    }

    return frameData;
};

Pipeline.updateVisualizations = function(p5, frameData, state, uiControls) {
    const startTime = performance.now();
    if (!state.toggles.viz) { updateStat('viz', 'Disabled'); return frameData; }
    const bs = uiControls.blockSize.value();
    const { diff, inputs, viz, ref } = state.buffers;
    if(!diff || !inputs || !viz || !ref) return frameData;
    diff.background(0);
    state.lastFrameDecisions.forEach(d => {
        const block = inputs.get(d.gx*bs,d.gy*bs,bs,bs);
        diff.push();
        if(d.blockDecision==='interpolate') diff.tint(255,127); else diff.filter(p5.INVERT);
        diff.image(block,d.gx*bs,d.gy*bs,bs,bs);
        diff.pop();
    });
    const counts={};
    state.lastFrameDecisions.forEach(d=>{if(d.blockDecision==='interpolate' && d.refPos){const k=`${d.refPos.x},${d.refPos.y}`;counts[k]=(counts[k]||0)+1;}});
    const sorted=Object.entries(counts).sort((a,b)=>b[1]-a[1]);
    viz.background(50);
    if (state.topTilesVizImageBitmap) {
        viz.image(state.topTilesVizImageBitmap, 0, 0);
    }
    frameData.timers.viz = performance.now() - startTime;
    updateStat('viz', `Decisions: ${state.lastFrameDecisions.length}\nTime: ${frameData.timers.viz.toFixed(1)}ms`);
    console.log(`Viz Time: ${frameData.timers.viz.toFixed(1)}ms`);
    return frameData;
};