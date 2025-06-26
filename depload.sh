#!/bin/bash

# A script to set up the 'prawncessing' development environment with corrected dependencies.

echo "--- Starting Prawncessing Setup (Revised) ---"

# Step 1: Ensure uv is installed
echo "[1/4] Checking for uv..."
if ! command -v uv &> /dev/null
then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
    echo "uv installed. You may need to restart your shell for the command to be in your PATH."
else
    echo "uv is already installed."
fi

# Step 2: Create project directory structure
echo "[2/4] Creating project directory structure at ~/prawncessing/src..."
mkdir -p ~/prawncessing/src
cd ~/prawncessing

# Step 3: Download corrected dependencies into ./src
echo "[3/4] Downloading required libraries..."

# p5.js Core Library (Using a recent, stable version - 1.9.4 for stability, as 2.x is very new)
# The DOM library is now included in the core file.
curl -o src/p5.min.js https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js

# OpenCV.js (v4.11.0, as per documentation)
curl -o src/opencv.js https://docs.opencv.org/4.11.0/opencv.js

echo "Libraries downloaded successfully."

# Step 4: Create placeholder HTML and JS files
echo "[4/4] Creating placeholder index.html and src/sketch.js..."

# Create index.html with corrected script loading
cat > index.html << EOL
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prawncessing - Real-Time Schematic Explorer</title>
    <style>
      body { padding: 0; margin: 0; background-color: #333; }
      main { display: flex; justify-content: center; align-items: center; height: 100vh; }
    </style>
    <script async src="src/opencv.js" onload="onOpenCvReady();" type="text/javascript"></script>
    
    <!-- Load the single p5.js core library. The DOM functionality is included. -->
    <script src="src/p5.min.js"></script>

    <!-- Load our sketch code last -->
    <script src="src/sketch.js"></script>
  </head>
  <body>
    <main></main>
  </body>
</html>
EOL

# Create src/sketch.js (no changes needed here from before)
cat > src/sketch.js << EOL
// A global flag to track if OpenCV is ready.
let cvReady = false;

// This function is called by the 'onload' attribute in our index.html
function onOpenCvReady() {
  console.log("OpenCV.js script loaded.");
  cv.onRuntimeInitialized = () => {
    console.log("OpenCV runtime initialized.");
    cvReady = true;
    document.body.style.backgroundColor = '#dff0d8'; // Visual confirmation
  };
}

function setup() {
  createCanvas(640, 480);
  pixelDensity(1);
  console.log("p5.js setup complete. Waiting for OpenCV...");
}

function draw() {
  if (!cvReady) {
    background(100);
    fill(255);
    textAlign(CENTER, CENTER);
    textSize(20);
    text("Loading OpenCV.js...", width / 2, height / 2);
    return;
  }

  background(51);
  fill(255);
  textAlign(LEFT, TOP);
  textSize(16);
  text("OpenCV is ready. Begin processing.", 10, 10);

  // --- Phase 1 implementation will start here ---
}
EOL

echo ""
echo "--- Setup Complete ---"
echo "Project created in '~/prawncessing'."
echo "To start the local server, run from '~/prawncessing':"
echo ""
echo "uv run python -m http.server"
echo ""
echo "Then, open http://0.0.0.0:8000 in your browser."