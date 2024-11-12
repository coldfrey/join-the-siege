import os
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from docx import Document
import pandas as pd

def preprocess_image(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    return thresh1

def pdf_to_txt(file_path, txt_path):
    images = convert_from_path(file_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for i, image in enumerate(images):
            processed_image = preprocess_image(image)
            text = pytesseract.image_to_string(processed_image, config='--oem 1')
            f.write(text)
            if i < len(images) - 1:
                f.write("\f")

def image_to_txt(file_path, txt_path):
    image = Image.open(file_path)
    processed_image = preprocess_image(image)
    text = pytesseract.image_to_string(processed_image, config='--oem 1')
    text = pytesseract.image_to_string(image, config='--oem 1')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

def word_to_txt(file_path, txt_path):
    document = Document(file_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for paragraph in document.paragraphs:
            f.write(paragraph.text + '\n')

def excel_to_txt(file_path, txt_path):
    df = pd.read_excel(file_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(df.to_string(index=False))

def process_file(file_path, txt_path, ext):
    try:
        if ext == '.pdf':
            pdf_to_txt(file_path, txt_path)
        elif ext in ['.jpg', '.png']:
            image_to_txt(file_path, txt_path)
        elif ext == '.docx':
            word_to_txt(file_path, txt_path)
        elif ext == '.xlsx':
            excel_to_txt(file_path, txt_path)
        else:
            return None
    finally:
        # Clean up the temporary file
        os.remove(file_path)

    # Read the extracted text back for return if needed
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()
