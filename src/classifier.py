from werkzeug.datastructures import FileStorage

# import ocr python file
from src.ocr import pdf_to_txt, image_to_txt, word_to_txt, excel_to_txt

def classify_file_by_name(file: FileStorage):
    filename = file.filename.lower()
    # file_bytes = file.read()

    if "drivers_license" in filename:
        return "drivers_licence"

    if "bank_statement" in filename:
        return "bank_statement"

    if "invoice" in filename:
        return "invoice"
    
    return "unknown file"

