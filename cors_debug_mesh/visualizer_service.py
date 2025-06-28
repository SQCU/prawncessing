from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def serve_visualizer():
    return send_from_directory('.', 'visualizer.html')

if __name__ == '__main__':
    app.run(port=5009)
