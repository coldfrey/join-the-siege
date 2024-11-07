from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import os
from src.constants import POSSIBLE_FILE_TYPES, OUTPUT_DIR



# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize Llama 3 (Ollama) model
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
llm = Ollama(model="llama3", callback_manager=callback_manager)


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