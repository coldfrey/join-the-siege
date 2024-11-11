import modal
from flask import Flask, request, jsonify
from src.ocr import process_file
from src.classifier import classify_file_by_name
from src.ai_assistants import classify_with_llama
from src.constants import ALLOWED_EXTENSIONS, OUTPUT_DIR
import os
from PyPDF2 import PdfReader, PdfWriter
from docx import Document
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = modal.App("classifier-flask-app")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"],
    storage_uri="memory://",
)

LARGE_PAGE_COUNT = 5  # Threshold for page count

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def trim_pdf_to_first_five_pages(input_path, output_path):
    """Trim the PDF to the first five pages if it has more than five."""
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copy only the first five pages if there are more
    for page_num in range(min(LARGE_PAGE_COUNT, len(reader.pages))):
        writer.add_page(reader.pages[page_num])

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

def trim_docx_to_first_five_paragraphs(input_path, output_path):
    """Trim the DOCX to the first five paragraphs if it has more than five."""
    document = Document(input_path)
    new_doc = Document()

    # Copy only the first five paragraphs
    for paragraph in document.paragraphs[:LARGE_PAGE_COUNT]:
        new_doc.add_paragraph(paragraph.text)

    new_doc.save(output_path)

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

    # Save the file temporarily
    file_extension = os.path.splitext(file.filename)[1].lower()
    temp_file_path = os.path.join('temp_uploads', file.filename)
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    file.save(temp_file_path)

    # Trim the file if necessary
    trimmed_file_path = temp_file_path
    if file_extension == '.pdf':
        reader = PdfReader(temp_file_path)
        if len(reader.pages) > LARGE_PAGE_COUNT:
            trimmed_file_path = temp_file_path.replace('.pdf', '_trimmed.pdf')
            trim_pdf_to_first_five_pages(temp_file_path, trimmed_file_path)
    elif file_extension == '.docx':
        document = Document(temp_file_path)
        if len(document.paragraphs) > LARGE_PAGE_COUNT:
            trimmed_file_path = temp_file_path.replace('.docx', '_trimmed.docx')
            trim_docx_to_first_five_paragraphs(temp_file_path, trimmed_file_path)

    # Proceed with normal processing
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.txt")
    extracted_data = process_file(trimmed_file_path, txt_filename, file_extension)
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

if __name__ == '__main__':
    app.run(debug=True)
