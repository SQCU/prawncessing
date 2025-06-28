const video = document.getElementById('video');
const inputCanvas = document.getElementById('input');
const outputCanvas = document.getElementById('output');
const inputCtx = inputCanvas.getContext('2d');
const outputCtx = outputCanvas.getContext('2d');

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
        video.play();
        processFrame();
    });

async function processFrame() {
    console.log("processFrame called");
    inputCtx.drawImage(video, 0, 0, inputCanvas.width, inputCanvas.height);
    const imageData = inputCanvas.toDataURL('image/png');
    
    // Remove the data URL prefix to send only the Base64 data
    const base64Data = imageData.replace(/^data:image\/png;base64,/, '');

    console.log("Sending frame to API");
    const response = await fetch('/api/v1/process-frame', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: base64Data })
    });

    if (response.ok) {
        console.log("API response OK");
        const imageBlob = await response.blob();
        const imageUrl = URL.createObjectURL(imageBlob);
        const image = new Image();
        image.onload = () => {
            console.log("Drawing image to output canvas");
            outputCtx.drawImage(image, 0, 0, outputCanvas.width, outputCanvas.height);
        };
        image.src = imageUrl;
    } else {
        console.error('Error processing frame:', response.status, await response.text());
    }

    requestAnimationFrame(processFrame);
}

video.addEventListener('play', () => {
    console.log("Video play event listener triggered");
    processFrame();
});
