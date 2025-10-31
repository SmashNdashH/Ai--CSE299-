import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
# Import language detection
from langdetect import detect, LangDetectException

# --- Global variables to hold RAG components ---
llm = None
retriever = None
format_docs = None
QA_PROMPT_BN = None
QA_PROMPT_EN = None

# --- Define format_docs function globally ---
def format_docs_func(docs):
    """Helper function to format retrieved documents."""
    return "\n\n".join(doc.page_content for doc in docs)

def load_rag_components():
    """
    Loads all components needed for RAG and stores them globally.
    This function will run once when the server starts.
    """
    global llm, retriever, format_docs, QA_PROMPT_BN, QA_PROMPT_EN

    print("Loading components for RAG...")

    # --- 1. Load the Vector Store ---
    folder_path = "faiss_index"
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}

    print(f"Loading embeddings model: {model_name}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    print(f"Loading vector store from {folder_path}...")
    try:
        loaded_vectorstore = FAISS.load_local(
            folder_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        retriever = loaded_vectorstore.as_retriever(search_kwargs={"k": 4})
        # Assign the global format_docs variable
        format_docs = format_docs_func
        
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return False
    
    print("Vector store loaded successfully.")

    # --- 2. Setup the LLM ---
    print("Initializing Ollama LLM (smollm2:360m)...")
    try:
        # Define LLM without system prompt here, we add it dynamically
        llm = ChatOllama(
            model="smollm2:360m",
            temperature=0.1
        )
        # Test connection
        llm.invoke("Hello")
        print("Ollama connection successful.")
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return False

    # --- 3. Define Prompt Templates ---
    # Bengali Prompt
    template_bn = """[SYSTEM]: আপনি একজন সহায়ক সহকারী যিনি সর্বদা বাংলা ভাষায় উত্তর দিবেন।

    নিম্নলিখিত প্রসঙ্গ ব্যবহার করে প্রশ্নের উত্তর দিন:

    {context}

    যদি আপনি উত্তর না জানেন, তবে শুধু বাংলায় বলুন "আমি এই প্রশ্নের উত্তর জানি না"।

    নির্দেশাবলী:
    - অবশ্যই শুধুমাত্র বাংলা ভাষায় উত্তর দিন
    - সর্বোচ্চ তিনটি বাক্য ব্যবহার করুন
    - সংক্ষিপ্ত এবং সুনির্দিষ্ট উত্তর দিন
    - প্রদত্ত তথ্যের বাইরে যাবেন না

    প্রশ্ন: {question}

    উত্তর:"""
    QA_PROMPT_BN = PromptTemplate.from_template(template_bn)

    # English Prompt
    template_en = """[SYSTEM]: You are a helpful assistant that MUST always respond in English.

    Use the following context to answer the question:

    {context}

    If you don't know the answer, just say "I don't know the answer to this question" in English.

    Instructions:
    - MUST answer only in English.
    - Use a maximum of three sentences.
    - Keep the answer concise and specific.
    - Do not go beyond the provided information.

    Question: {question}

    Answer:"""
    QA_PROMPT_EN = PromptTemplate.from_template(template_en)
    
    print("✅ RAG components are ready.")
    return True


# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles chat requests, detects language, and uses the appropriate prompt.
    """
    global llm, retriever, format_docs, QA_PROMPT_BN, QA_PROMPT_EN
    
    # Check if components are loaded
    if not all([llm, retriever, format_docs, QA_PROMPT_BN, QA_PROMPT_EN]):
        return jsonify({"error": "RAG components are not loaded. Check server logs."}), 500

    try:
        data = request.json
        user_message = data.get('message')

        if not user_message:
            return jsonify({"error": "No 'message' found in request"}), 400

        print(f"Received query: {user_message}")

        # --- Language Detection ---
        detected_lang = 'bn' # Default to Bengali
        try:
            # Only detect if message is reasonably long
            if len(user_message.strip()) > 10: 
                detected_lang = detect(user_message)
            print(f"Detected language: {detected_lang}")
        except LangDetectException:
            print("Language detection failed, defaulting to Bengali.")
            detected_lang = 'bn'
        except Exception as lang_e:
             print(f"An unexpected error occurred during language detection: {lang_e}. Defaulting to Bengali.")
             detected_lang = 'bn'


        # --- Retrieve Context ---
        try:
            # --- THIS IS THE CORRECTED LINE ---
            retrieved_docs = retriever.invoke(user_message) 
            # --- END CORRECTION ---
            context_text = format_docs(retrieved_docs)
            # Optional: Print retrieved context for debugging
            # print("\n--- Retrieved Context ---")
            # print(context_text)
            # print("-------------------------\n")
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return jsonify({"error": "Failed to retrieve relevant context."}), 500

        # --- Choose Prompt and Format ---
        if detected_lang == 'bn':
            prompt_template = QA_PROMPT_BN
            print("Using Bengali prompt.")
        else: # Default to English for 'en' and any other detected language
            prompt_template = QA_PROMPT_EN
            print("Using English prompt.")
            
        formatted_prompt = prompt_template.format(context=context_text, question=user_message)

        # --- Invoke LLM ---
        try:
            ai_response = llm.invoke(formatted_prompt)
            # ChatOllama response is often in the 'content' attribute
            bot_response = ai_response.content if hasattr(ai_response, 'content') else str(ai_response) 

        except Exception as e:
            print(f"Error during LLM invocation: {e}")
            return jsonify({"error": f"LLM failed to generate response: {e}"}), 500

        print(f"Sending response: {bot_response}")
        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Load RAG components *before* starting the server
    if load_rag_components():
        print("\n--- Starting Flask Server ---")
        print("Your RAG chatbot is now available at http://localhost:5000")
        print("Your frontend can send POST requests to http://localhost:5000/chat")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("\nFailed to load RAG components. Server will not start.")