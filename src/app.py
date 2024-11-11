from flask import Flask, request, jsonify, Response
from src.ocr import process_file
from src.classifier import classify_file_by_name
from src.ai_assistants import classify_with_llama
from src.constants import ALLOWED_EXTENSIONS, OUTPUT_DIR
import os
from PIL import Image
import PyPDF2
from docx import Document
import pandas as pd
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"],
    storage_uri="memory://",
)

LARGE_FILE_SIZE_MB = 50  # Define a threshold for large file size in megabytes
PDF_LARGE_FILE_SIZE_MB = 10  # Define a threshold for large PDF file size in megabytes
LARGE_PAGE_COUNT = 5  # Define a threshold for large page count

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Get the size of the uploaded file in MB."""
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)  # Convert bytes to megabytes
    file.seek(0)  # Reset file pointer
    return size_mb

@app.route('/classify_file', methods=['POST'])
@limiter.limit("10 per hour")
def classify_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Check for large file size
    file_size_mb = get_file_size(file)
    if file_size_mb > LARGE_FILE_SIZE_MB or file_size_mb > PDF_LARGE_FILE_SIZE_MB:
        # Send a warning message but continue processing
        warning_response = jsonify({
            "message": "Large file detected. This would take a few minutes to process... retry with the large_file_route",
            # provide the large file route to handle the large file
            "large_file_route": "/classify_large_file"
        })
        warning_response.status_code = 202
        return warning_response

    # Save the file temporarily
    file_extension = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join('temp_uploads', file.filename)
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    file.save(temp_file_path)

    # Proceed with normal processing
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.txt")
    extracted_data = process_file(temp_file_path, txt_filename, file_extension)
    print("Finished OCR, extracted data: ", extracted_data)

    # Classify the document by file name
    document_type_by_name = classify_file_by_name(file)
    print("Finished classification by name, document type: ", document_type_by_name)

    # Classify the document using Llama 3
    if not extracted_data:
        document_type, reasoning = 'unknown file', 'Unable to extract data from the file'
    else:
        document_type, reasoning = classify_with_llama(extracted_data)

    return jsonify({
        "document_type_from_llama": document_type,
        "llama_text_ai_classification": reasoning,
        "classified_file_name": document_type_by_name,
        "filename": file.filename
    }), 200

@app.route('/classify_large_file', methods=['POST'])
def classify_large_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Save the file temporarily
    file_extension = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join('temp_uploads', file.filename)
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    file.save(temp_file_path)

    # Proceed with normal processing
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.txt")
    extracted_data = process_file(temp_file_path, txt_filename, file_extension)
    print("Finished OCR, extracted data: ", extracted_data)

    # Classify the document by file name
    document_type_by_name = classify_file_by_name(file)
    print("Finished classification by name, document type: ", document_type_by_name)

    if not extracted_data:
        document_type, reasoning = 'unknown file', 'Unable to extract data from the file'
    else:
        document_type, reasoning = classify_with_llama(extracted_data)

    return jsonify({
        "document_type_from_llama": document_type,
        "llama_text_ai_classification": reasoning,
        "classified_file_name": document_type_by_name,
        "filename": file.filename
    }), 200
if __name__ == '__main__':
    app.run(debug=True)
