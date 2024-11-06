import os
import json
import itertools
import threading
import time
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager

# Initialize embedding function
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Ensure API key is set
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Load the vector store
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_model)

# Setup retrieval system
retriever = vectorstore.as_retriever()

# Define a function to format retrieved documents for input into the LLM
def format_docs(docs):
    context = "\n\n".join(doc.page_content + "\n" for doc in docs)
    return context

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

# Initialize the language model
llm = Ollama(model="llama3", callback_manager=callback_manager)

# Create a retrieval and response generation chain
prompt = hub.pull("rlm/rag-prompt")

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Function to display a simple spinner
def spinner():
    for frame in itertools.cycle('|/-\\'):
        if not spinner.run:
            break
        print(f'\rProcessing... {frame}', end='')
        time.sleep(0.2)
    print('\r', end='')  # Clean up the spinner line

spinner.run = True

# Interactive shell for RAG chat
while True:
    user_input = input("\n\nAsk a question: ")
    if user_input.lower() in ["quit", "exit"]:
        break
    
    # Start spinner in a separate thread
    # spinner.run = True
    # spin_thread = threading.Thread(target=spinner)
    # spin_thread.start()
    
    # Invoke the chain to generate a response
    response = rag_chain.invoke(user_input)
    
    # Stop spinner
    # spinner.run = False
    # spin_thread.join()
    
    # print(f"Response: {response}\n")

print("Exiting RAG Chat.")
