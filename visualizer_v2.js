// Service URLs
const PROXY_SERVER = "http://localhost:5008";
const VIDEO_STREAM_MOCK_SERVER = `${PROXY_SERVER}/videostream_mock_server`;
const IMAGE_INPUT_SERVICE = `${PROXY_SERVER}/image_input_service`;
const DCT_SERVICE = `${PROXY_SERVER}/dct_service`;
const REFERENCE_FRAME_SERVICE = `${PROXY_SERVER}/reference_frame_service`;
const DIFFERENCE_SERVICE = `${PROXY_SERVER}/difference_service`;
const ACCUMULATOR_SERVICE = `${PROXY_SERVER}/accumulator_service`;

// Canvas elements
const inputCanvas = document.getElementById('inputCanvas');
const imageInputCanvas = document.getElementById('imageInputCanvas');
const forwardDctCanvas = document.getElementById('forwardDctCanvas');
const referenceFrameCanvas = document.getElementById('referenceFrameCanvas');
const differenceCanvas = document.getElementById('differenceCanvas');
const accumulatorCanvas = document.getElementById('accumulatorCanvas');

const ctxInput = inputCanvas.getContext('2d');
const ctxImageInput = imageInputCanvas.getContext('2d');
const ctxForwardDct = forwardDctCanvas.getContext('2d');
const ctxReferenceFrame = referenceFrameCanvas.getContext('2d');
const ctxDifference = differenceCanvas.getContext('2d');
const ctxAccumulator = accumulatorCanvas.getContext('2d');

// Helper function to clear canvas
function clearCanvas(ctx, canvas) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

// Helper function to draw text on canvas
function drawText(ctx, canvas, text) {
    clearCanvas(ctx, canvas);
    ctx.fillStyle = 'black';
    ctx.font = '14px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);
}

// Function to fetch data from a service
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        // Check if content-type is image/jpeg
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("image/jpeg")) {
            return response.blob(); // Return blob for image
        } else {
            return response.json(); // Assume JSON for other data
        }
    } catch (error) {
        console.error(`Could not fetch from ${url}:`, error);
        return null;
    }
}

// Visualization functions
async function visualizeInput() {
    const imageData = await fetchData(`${VIDEO_STREAM_MOCK_SERVER}/frame`);
    if (imageData) {
        const img = new Image();
        img.onload = () => {
            clearCanvas(ctxInput, inputCanvas);
            // Draw image, scaling to fit canvas while maintaining aspect ratio
            const aspectRatio = img.width / img.height;
            let drawWidth = inputCanvas.width;
            let drawHeight = inputCanvas.width / aspectRatio;

            if (drawHeight > inputCanvas.height) {
                drawHeight = inputCanvas.height;
                drawWidth = inputCanvas.height * aspectRatio;
            }
            const x = (inputCanvas.width - drawWidth) / 2;
            const y = (inputCanvas.height - drawHeight) / 2;
            ctxInput.drawImage(img, x, y, drawWidth, drawHeight);
        };
        img.src = URL.createObjectURL(imageData);
    } else {
        drawText(ctxInput, inputCanvas, "No input frame");
    }
}

async function visualizeImageInput() {
    const data = await fetchData(`${IMAGE_INPUT_SERVICE}/latest_frame`);
    if (data && data.latest_frame) {
        drawText(ctxImageInput, imageInputCanvas, `Frame: ${data.latest_frame}`);
    } else {
        drawText(ctxImageInput, imageInputCanvas, "No image input data");
    }
}

async function visualizeForwardDct() {
    const data = await fetchData(`${DCT_SERVICE}/latest_forward_dct`);
    if (data && data.latest_dct) {
        drawText(ctxForwardDct, forwardDctCanvas, `DCT: ${data.latest_dct}`);
    } else {
        drawText(ctxForwardDct, forwardDctCanvas, "No forward DCT data");
    }
}

async function visualizeReferenceFrame() {
    const data = await fetchData(`${REFERENCE_FRAME_SERVICE}/latest_reference_frame`);
    if (data && data.latest_reference_frame) {
        drawText(ctxReferenceFrame, referenceFrameCanvas, `Ref: ${data.latest_reference_frame}`);
    } else {
        drawText(ctxReferenceFrame, referenceFrameCanvas, "No reference frame");
    }
}

async function visualizeDifference() {
    const data = await fetchData(`${DIFFERENCE_SERVICE}/latest_difference`);
    if (data && data.latest_difference) {
        drawText(ctxDifference, differenceCanvas, `Diff: ${data.latest_difference}`);
    } else {
        drawText(ctxDifference, differenceCanvas, "No difference data");
    }
}

async function visualizeAccumulator() {
    const data = await fetchData(`${ACCUMULATOR_SERVICE}/get_accumulated_frame`);
    if (data && data.accumulated_frame) {
        drawText(ctxAccumulator, accumulatorCanvas, `Accum: ${data.accumulated_frame}`);
    } else {
        drawText(ctxAccumulator, accumulatorCanvas, "No accumulated data");
    }
}

// Main update loop
function updateVisualizations() {
    visualizeInput();
    visualizeImageInput();
    visualizeForwardDct();
    visualizeReferenceFrame();
    visualizeDifference();
    visualizeAccumulator();
}

// Initial clear and start update loop
clearCanvas(ctxInput, inputCanvas);
clearCanvas(ctxImageInput, imageInputCanvas);
clearCanvas(ctxForwardDct, forwardDctCanvas);
clearCanvas(ctxReferenceFrame, referenceFrameCanvas);
clearCanvas(ctxDifference, differenceCanvas);
clearCanvas(ctxAccumulator, accumulatorCanvas);

setInterval(updateVisualizations, 1000); // Update every 1 second
