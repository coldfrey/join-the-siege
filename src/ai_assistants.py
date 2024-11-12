from src.constants import POSSIBLE_FILE_TYPES
import os
from src.app import Model

def classify_with_llama(extracted_text):
    # Create a prompt for Llama 3 to classify the document
    prompt = (
        f"Classify the following document based on its content. Possible types are: {', '.join(POSSIBLE_FILE_TYPES)}.\n\n"
        f"Document Content:\n{extracted_text}\n\n"
        "Return the classification as follows in this exact format: 'Document Type: [Type]', Reasoning: [Reasoning]."
    )

    model = Model()
    response = model.classify_with_llama.remote(prompt)
    print("Model response:", response)

    # Parse the response to separate "Document Type" and "Reasoning"
    document_type = ""
    reasoning = ""

    # Split the response using known prefixes
    lines = response.split(", Reasoning: ")
    if len(lines) == 2:
        document_type = lines[0].replace("Document Type: ", "").strip()
        reasoning = lines[1].strip()
    else:
        # Handle unexpected response format
        document_type = "Unknown"
        reasoning = response

    return document_type, reasoning
