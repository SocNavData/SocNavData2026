import datetime
import json
import re
import os

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# storage directory for received data
STORAGE_DIR = "/workspaces/hunavsim_devcontainer/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

print("Started!")

@app.route('/')
def home():
    return send_file('static/index.html')

@app.route('/instructions.mp4')
def instructions_mp4():
    return send_file('static/instructions.mp4')

@app.route('/indices.txt')
def indices_txt():
    path_indices = 'static/indices.txt'
    if os.path.exists(path_indices):
        return send_file(path_indices)
    return "Not found", 404
@app.route('/instructions.webm')
def instructions_webm():
    return send_file('static/instructions.webm')

@app.route('/surveycode.py')
def survey():
    return send_file('static/surveycode.py')

@app.route('/slider.py')
def slider():
    return send_file('static/slider.py')

@app.route('/tasks.py')
def tasks():
    return send_file('static/tasks.py')

@app.route('/submit', methods=['PUT', 'POST'])
def submit():
    #print("headers", request.headers)
    #print("data", request.data)
    data = str(request.data.decode('UTF-8'))

    print(f"GOT: {len(data)}")
    if len(data) < 10_000_000:
        now = datetime.datetime.now()
        path = "/workspaces/hunavsim_devcontainer/storage/" + str(now.strftime("%Y-%m-%d_%H:%M:%S"))+".json"
        #path_indices = os.path.join(STORAGE_DIR, "indices.txt")
        path_indices = "/workspaces/hunavsim_devcontainer/src/SocNavData2026/survey_code/app/static/indices.txt"
        # Write the raw data
        fd = open(path, "w")
        fd.write(data)
        fd.close()
        
        # Extract indices field using regex - can be either a string or an array
        # Try to match array format first: "indices": [...]
        indices_match = re.search(r'"indices"\s*:\s*(\[[^\]]*\])', data)
        if indices_match:
            data_indices = indices_match.group(1)
            with open(path_indices, "w") as fd_indices:
                    fd_indices.write(data_indices)
            print(f"Extracted indices (array): {data_indices[:100]}...")
        else:
            # Try string format: "indices": "..."
            indices_match = re.search(r'"indices"\s*:\s*"([^"]*)"', data)
            if indices_match:
                data_indices = indices_match.group(1)
                with open(path_indices, "w") as fd_indices:
                    fd_indices.write(data_indices)
                print(f"Extracted indices (string): {data_indices}")
            else:
                print("Could not find 'indices' field in data")
        # log a small preview of saved indices
        try:
            with open(path_indices, "r") as nunzio:
                preview = nunzio.read(200)
            print("Saved indices preview:", preview)
        except Exception as e:
            print("Could not read saved indices:", e)
        return "Received", 200

@app.route('/log', methods=['POST'])
def log():
    payload = request.get_json(silent=True)
    if payload is None:
        message = request.data.decode('UTF-8', errors='replace')
    else:
        message = json.dumps(payload)

    preview = message if len(message) <= 2000 else message[:2000] + "... (truncated)"
    print(f"LOG: {preview}")
    return "OK", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
