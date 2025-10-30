from flask_cors import CORS
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
# ------------------------
# LangChain imports (0.3.7)
# ------------------------
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
load_dotenv()

# We need to change the API endpoint name used by the extension from '/chat' to '/ask'
# to match the generic 'sendMessage' function in the extension code.

app = Flask(__name__, static_folder='../frontend', static_url_path='')
# ----------------------------------------------------------------------
# 📌 CRUCIAL CHANGE: Configure CORS to only allow Nirma University domains
# Note: You need to specify ALL origins that will access your API.
# The extension runs *on* these domains, so they are the origins.
# ----------------------------------------------------------------------
CORS(app, resources={
    r"/ask": {"origins": [
        "https://nirmauni.ac.in", 
        "https://www.nirmauni.ac.in", 
        "http://127.0.0.1:5000" # Keep for local testing if needed
    ]},
    r"/health": {"origins": "*"} # Health check can be public
})
# ----------------------------------------------------------------------


vectorstore = None
qa_chain = None

def initialize_chatbot():
    global vectorstore, qa_chain

    print("🚀 Initializing Nirma University Chatbot...")

    # Embeddings
    print("📦 Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    # Load vectorstore
    print("📂 Loading vector store...")
    vectorstore_path = "data/vectorstore"
    if not os.path.exists(vectorstore_path):
        print("❌ Vector store not found! Please run embeddings.py first.")
        return False

    vectorstore = FAISS.load_local(
        vectorstore_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Initialize LLM (Gemini 2.0 Flash)
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in the environment")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        google_api_key=gemini_api_key
    )

    template = """You are a helpful AI assistant for Nirma University. 
Use the following context from the university's website to answer the question.
If you don't know the answer based on the context, say "I don't have that information in my knowledge base. Please contact the university directly at admissions@nirmauni.ac.in or call +91-2717-241911."
Context: {context}

Question: {question}

Provide a clear, concise, and friendly answer. If relevant, include specific details like dates, requirements, or contact information.
Answer:"""

    PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )

    # Create QA chain
    print("🔗 Creating QA chain...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    print("✅ Chatbot initialized successfully!\n")
    return True

# ------------------------
# Flask endpoints
# ------------------------
@app.route('/')
def index():
    # Only useful if you are serving a frontend from the same server, 
    # which is not the case for a Chrome extension.
    return "Nirma University Chatbot API is running."

@app.route('/api/health', methods=['GET'])
def home():
    return jsonify({"status": "running", "message": "Nirma University Chatbot API", "version": "1.0"})

# ----------------------------------------------------------------------
# 📌 IMPORTANT: Renaming the endpoint from '/chat' to '/ask' 
# to match the request used in the 'content.js' file provided earlier.
# The payload is also simplified to match the extension's JS.
# ----------------------------------------------------------------------
@app.route('/ask', methods=['POST'])
def chat():
    # Note: The extension sends payload as {input: "..."}
    try:
        data = request.get_json()
        user_message = data.get("input", "").strip() # Use 'input' key

        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        # Get response from QA chain
        print(f"📥 Query: {user_message}")
        result = qa_chain.invoke({"query": user_message})

        answer = result["result"]
        # Source documents are often too verbose for a chat response, 
        # but you can decide to format them better later.
        sources = [doc.metadata.get("source", "Unknown") for doc in result.get("source_documents", [])]

        print(f"📤 Response: {answer[:100]}...")
        # Note: The extension expects the key 'response'
        return jsonify({"response": answer, "sources": sources[:3], "status": "success"})

    except Exception as e:
        print(f" Error: {e}")
        return jsonify({"error": "An error occurred processing your request", "details": str(e)}), 500

# ----------------------------------------------------------------------
# Renamed endpoint to '/health' and removed the quick-answer one 
# as it's not strictly necessary for the core extension functionality.
# ----------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "vectorstore_loaded": vectorstore is not None,
        "qa_chain_ready": qa_chain is not None
    })

# ------------------------
# Run server
# ------------------------
if __name__ == "__main__":
    if initialize_chatbot():
        print("🌐 Starting Flask server at http://localhost:5000")
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        print("❌ Failed to initialize chatbot. Exiting...")
