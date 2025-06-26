// ------------ GLOBAL VARIABLES ------------- //
let imgStream; 
let refBuffer; 

const BLOCK_SIZE = 32;
let showDiagnostics = true;

// ------------ P5.JS SETUP FUNCTION ------------- //
function setup() {
  createCanvas(640, 480);
  pixelDensity(1);
  
  imgStream = createCapture(VIDEO);
  imgStream.size(width, height);
  imgStream.hide();

  refBuffer = createGraphics(width, height);
  refBuffer.pixelDensity(1);
  
  // Initialize REF with a blank frame
  refBuffer.background(0);

  console.log("Full pipeline implemented. Press 's' to set the REF frame.");
  console.log("Press 'd' to toggle diagnostic text.");
}

// ------------ P5.JS DRAW LOOP ------------- //
function draw() {
  // We don't clear the background, we will draw over every pixel.
  
  // Check if the video is ready
  if (imgStream.width === 0) {
    background(0);
    fill(255);
    textAlign(CENTER, CENTER);
    text("Waiting for video stream...", width / 2, height / 2);
    return;
  }
  
  // Loop through the image in block-sized steps
  for (let y = 0; y < height; y += BLOCK_SIZE) {
    for (let x = 0; x < width; x += BLOCK_SIZE) {
      
      // 1. Get corresponding blocks from IMG and REF streams
      let imgBlock = imgStream.get(x, y, BLOCK_SIZE, BLOCK_SIZE);
      let refBlock = refBuffer.get(x, y, BLOCK_SIZE, BLOCK_SIZE);
      
      // 2. Apply DCT to both blocks
      let imgDCT = applyDCT(imgBlock);
      let refDCT = applyDCT(refBlock);
      
      // 3. Calculate the Difference
      // For now, we hardcode the 'subtract' mode
      let diffDCT = calculateDiff(imgDCT, refDCT, 'subtract');
      
      // 4. Generate the Schedule
      // Hardcoding 'full_pass' to allow all data through
      let schedule = generateSchedule('full_pass', BLOCK_SIZE);
      
      // 5. Apply the Summer
      // This step reconstructs the image DCT using the reference and the difference.
      // This aligns with a compression/reconstruction interpretation (Scenario 1A).
      let outputDCT = applySummer(refDCT, diffDCT, schedule);
      
      // 6. Apply Inverse DCT to get the final pixel block
      let outputBlock = applyIDCT(outputDCT);
      
      // 7. Draw the reconstructed block to the canvas
      if (outputBlock) {
        image(outputBlock, x, y);
      }
    }
  }

  // --- Diagnostic Info ---
  if(showDiagnostics) {
    fill(0, 150);
    noStroke();
    rect(0, 0, width, 50);
    fill(255, 255, 0);
    textSize(14);
    textAlign(LEFT, TOP);
    text("OUTPUT: Full pipeline reconstruction", 10, 10);
    text("Press 's' to set REF frame | Press 'd' to hide this text", 10, 30);
  }
}

// ------------ INTERACTIVITY ------------- //
function keyPressed() {
  if (key === 's' || key === 'S') {
    console.log("Setting REF frame.");
    // Copy the current video frame into our reference buffer
    refBuffer.image(imgStream, 0, 0, width, height);
  }
  if (key === 'd' || key === 'D') {
    showDiagnostics = !showDiagnostics;
  }
}

// ------------ CORE SYSTEM COMPONENTS (IMPLEMENTED) ------------- //

// ... dct2D function remains the same as before ...
function dct2D(matrix, inverse = false) {
  const size = matrix.length;
  let intermediate = [];
  let final = [];
  for (let i = 0; i < size; i++) {
    intermediate[i] = dct(matrix[i], inverse);
  }
  for (let j = 0; j < size; j++) {
    let col = [];
    for (let i = 0; i < size; i++) {
      col.push(intermediate[i][j]);
    }
    let transformedCol = dct(col, inverse);
    for (let i = 0; i < size; i++) {
      if (!final[i]) final[i] = [];
      final[i][j] = transformedCol[i];
    }
  }
  return final;
}

function applyDCT(blockImage) {
  const size = blockImage.width;
  if (size === 0) return [];
  blockImage.loadPixels();
  let matrix = [];
  for (let y = 0; y < size; y++) {
    matrix[y] = [];
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      const gray = (blockImage.pixels[i] + blockImage.pixels[i + 1] + blockImage.pixels[i + 2]) / 3;
      matrix[y][x] = gray - 128;
    }
  }
  return dct2D(matrix);
}

function calculateDiff(dctBlock1, dctBlock2, diffMode) {
  const size = dctBlock1.length;
  let diff = [];
  for (let y = 0; y < size; y++) {
    diff[y] = [];
    for (let x = 0; x < size; x++) {
      // For now, only implementing 'subtract'
      diff[y][x] = dctBlock1[y][x] - dctBlock2[y][x];
    }
  }
  return diff;
}

function generateSchedule(scheduleMode, size) {
  let schedule = [];
  for (let y = 0; y < size; y++) {
    schedule[y] = [];
    for (let x = 0; x < size; x++) {
      // 'full_pass' mode: let all data through
      schedule[y][x] = 1;
    }
  }
  return schedule;
}

function applySummer(baseDCT, diffDCT, schedule) {
  const size = baseDCT.length;
  let outputDCT = [];
  for (let y = 0; y < size; y++) {
    outputDCT[y] = [];
    for (let x = 0; x < size; x++) {
      // Reconstruct: start with the base (REF) and add the scheduled difference
      outputDCT[y][x] = baseDCT[y][x] + (diffDCT[y][x] * schedule[y][x]);
    }
  }
  return outputDCT;
}

function applyIDCT(dctCoefficients) {
  if (!dctCoefficients || dctCoefficients.length === 0) return null;
  const size = dctCoefficients.length;
  let grayValues = dct2D(dctCoefficients, true);
  let resultImg = createImage(size, size);
  resultImg.loadPixels();
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      const val = grayValues[y][x] + 128;
      resultImg.pixels[i] = val;
      resultImg.pixels[i + 1] = val;
      resultImg.pixels[i + 2] = val;
      resultImg.pixels[i + 3] = 255;
    }
  }
  resultImg.updatePixels();
  return resultImg;
}