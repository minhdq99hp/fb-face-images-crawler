from flask import Flask, request, jsonify
from werkzeug import secure_filename
import os
import json
import zipfile


DATA_PATH = ''
TEMP_PATH = ''

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/get-filtered-friendlist", methods= ['POST', 'GET'])
def get_filtered_friendlist():
    if request.method == 'POST':
        data = request.get_json()

        friendlist = data['friendlist']

    for file_name in os.listdir(DATA_PATH):
        if os.path.isdir(os.path.join(DATA_PATH, file_name)):
            metadata_path = os.path.join(DATA_PATH, file_name, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path) as json_file:
                    metadata = json.load(json_file)

                    if metadata['state'] == 'done':
                        if metadata['id'] in friendlist:
                            friendlist.remove(metadata['id'])
                        print("filter " + metadata['id'])
    
    return_data = {"friendlist": friendlist}

    return jsonify(return_data)

@app.route("/upload-data", methods=['POST'])
def upload_data():
    if request.method == 'POST':
        data = request.files['data']
        zipfile_path = os.path.join(TEMP_PATH, secure_filename(data.filename))

        data.save(zipfile_path)

        # extract zip file to data folder
        with zipfile.ZipFile(zipfile_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_PATH)

        # remove files in temp folder
        os.remove(zipfile_path)

        return 'file uploaded successfully'

if __name__ == "__main__":
    f = open('config.json', 'r')
    config = json.load(f)
    f.close()
    DATA_PATH = config['data-path']
    TEMP_PATH = config['temp-path']


    app.run(debug=True, threaded=True)
