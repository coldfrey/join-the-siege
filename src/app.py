from flask import Flask, request, jsonify
from src.classifier import classify_file_by_name
from src.ocr import process_file
import os

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg'}
OUTPUT_DIR = 'outputs'

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/classify_file', methods=['POST'])
def classify_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    file_class = classify_file_by_name(file)

    # Process the file and save output in the specified directory
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.txt")
    extracted_data = process_file(file, txt_filename)

    return jsonify({
        "file_class": file_class,
        "extracted_data": extracted_data,
        "filename": file.filename
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
