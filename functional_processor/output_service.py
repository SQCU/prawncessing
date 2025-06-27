from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def _display_video_data(video_data: str) -> dict:
    """
    Pure function to handle displaying video data.
    In a real implementation, this would display the video_data.
    """
    print(f"Displaying video data: {video_data}")
    return {"status": "video displayed"}

@app.route('/display_video', methods=['POST'])
def display_video():
    # Placeholder for displaying video stream
    data = request.json
    video_data = data.get('video_data')
    if not video_data:
        return jsonify({"error": "Invalid request: 'video_data' is required."}), 400

    result = _display_video_data(video_data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5006)

# This service is an older output service and is not typically started by current orchestration scripts.

