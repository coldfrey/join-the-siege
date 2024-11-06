from flask import Flask, request, jsonify
from src.ocr import process_file
from src.classifier import classify_file_by_name
import os
from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}
OUTPUT_DIR = 'outputs'
POSSIBLE_FILE_TYPES = [
    "Invoice",
    "Contract",
    "Resume",
    "Report",
    "Letter",
    "Email",
    "Research Paper",
    "Form",
    "Memo",
    "Receipt",
    "Bank Statement",
    "Medical Record",
    "Legal Document",
    "Other"
]

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Llama 3 (Ollama) model
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
llm = Ollama(model="llama3", callback_manager=callback_manager)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def classify_with_llama(extracted_text):
    # Create a prompt for Llama 3 to classify the document
    prompt = (
        f"Classify the following document based on its content. Possible types are: {', '.join(POSSIBLE_FILE_TYPES)}.\n\n"
        f"Document Content:\n{extracted_text}\n\n"
        "Return the classification as follows in this exact format: 'Document Type: [Type]', Reasoning: [Reasoning]."
    )
    
    # Use Llama 3 to generate a classification
    response = llm(prompt).strip()
    
    # Parse the response to separate "Document Type" and "Reasoning"
    document_type = ""
    reasoning = ""

    # Split the response using known prefixes
    lines = response.split(", Reasoning: ")
    if len(lines) == 2:
        document_type = lines[0].replace("Document Type: ", "").strip()
        reasoning = lines[1].strip()

    return document_type, reasoning

@app.route('/classify_file', methods=['POST'])
def classify_file_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Process the file and save output in the specified directory
    txt_filename = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.txt")
    extracted_data = process_file(file, txt_filename)

    # Classify the document by file name
    document_type_by_name = classify_file_by_name(file)

    # Classify the document using Llama 3
    document_type, reasoning = classify_with_llama(extracted_data)

    return jsonify({
        "document_type_from_llama": document_type,
        "reasoning_from_llama": reasoning,
        "classified_file_name": document_type_by_name,
        "filename": file.filename
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
