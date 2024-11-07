from flask import Flask, request, jsonify, url_for
from src.ocr import process_file
from src.classifier import classify_file_by_name
from src.ollama import classify_with_llama
from src.constants import ALLOWED_EXTENSIONS, OUTPUT_DIR
import os
from PIL import Image
import PyPDF2
from docx import Document
import pandas as pd
from celery import Celery
import sys

app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

LARGE_FILE_SIZE_MB = 5
LARGE_PAGE_COUNT = 5

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return size_mb

def get_page_count(file_path, file_extension):
    if file_extension == '.pdf':
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        image = Image.open(file_path)
        return 1
    elif file_extension == '.docx':
        document = Document(file_path)
        return len(document.paragraphs)
    elif file_extension == '.xlsx':
        df = pd.ExcelFile(file_path)
        return len(df.sheet_names)
    return 0

@celery.task
def process_file_task(file_path, file_name):
    # This function will process the file in the background
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}.txt")
    extracted_data = process_file(file_path, txt_filename)
    document_type_by_name = classify_file_by_name(file_name)
    document_type, reasoning = classify_with_llama(extracted_data)

    return {
        "document_type_from_llama": document_type,
        "reasoning_from_llama": reasoning,
        "classified_file_name": document_type_by_name,
        "filename": file_name
    }

@app.route('/classify_file', methods=['POST'])
def classify_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    file_size_mb = get_file_size(file)
    if file_size_mb > LARGE_FILE_SIZE_MB:
        warning_message = "Large file detected. This may take a minute to process."
    else:
        warning_message = "Processing file."

    # Save the file temporarily to check the page count
    file_extension = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join('temp_uploads', file.filename)
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    file.save(temp_file_path)

    page_count = get_page_count(temp_file_path, file_extension)
    if page_count > LARGE_PAGE_COUNT:
        warning_message = "Large file detected. This may take a minute to process."

    # Start the background task
    task = process_file_task.apply_async(args=[temp_file_path, file.filename])

    return jsonify({
        "message": warning_message,
        "task_id": task.id,
        "status_url": url_for('get_task_status', task_id=task.id, _external=True)
    })

@app.route('/status/<task_id>')
def get_task_status(task_id):
    task = process_file_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            "state": task.state,
            "status": "Processing..."
        }
    elif task.state != 'FAILURE':
        response = {
            "state": task.state,
            "result": task.result
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info)
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
