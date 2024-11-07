from werkzeug.datastructures import FileStorage

# import ocr python file
from src.ocr import pdf_to_txt, image_to_txt, word_to_txt, excel_to_txt

def classify_file_by_name(file_name: str) -> str:
    filename = file_name.lower()
    # file_bytes = file.read()

    if "drivers_license" in filename:
        return "drivers_licence"

    if "bank_statement" in filename:
        return "bank_statement"

    if "invoice" in filename:
        return "invoice"
    
    if "resume" in filename:
        return "resume"
    
    if "contract" in filename:
        return "contract"
    
    if "report" in filename:
        return "report"
    
    if "letter" in filename:
        return "letter"
    
    if "email" in filename:
        return "email"
    
    if "research_paper" in filename:
        return "research_paper"
    
    if "form" in filename:
        return "form"
    
    if "memo" in filename:
        return "memo"
    
    if "receipt" in filename:
        return "receipt"
    
    if "medical_record" in filename:
        return "medical_record"
    
    if "legal_document" in filename:
        return "legal_document"
    
    return "unknown file"

