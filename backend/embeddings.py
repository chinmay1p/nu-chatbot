import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
from PyPDF2.errors import PdfReadError

class VectorStoreBuilder:
    def __init__(self, data_dir="data/raw", vectorstore_dir="data/vectorstore"):
        self.data_dir = data_dir
        self.vectorstore_dir = vectorstore_dir
        os.makedirs(vectorstore_dir, exist_ok=True)
        
        print("📦 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        print("✅ Embedding model loaded!")
    def load_documents(self):
        documents = []

        print(f"📁 Looking in: {self.data_dir}")
        print("📂 Files found:", os.listdir(self.data_dir))

        json_file = os.path.join(self.data_dir, "all_data.json")
        if os.path.exists(json_file):
            print("✅ Found all_data.json, loading from JSON")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    documents.append(Document(
                        page_content=item['content'],
                        metadata={'source': item['url'], 'title': item['title']}
                    ))
        else:
            for filename in os.listdir(self.data_dir):
                filepath = os.path.join(self.data_dir, filename)
                print("🔎 Checking:", filename)
                if filename.endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        documents.append(Document(page_content=f.read(), metadata={'source': filename}))
                elif filename.endswith('.pdf'):
                    print("📄 Loading PDF:", filename)
                    from langchain_community.document_loaders import PyPDFLoader
                    try:
                        with open(filepath, "rb") as f:
                            if not f.read(5).startswith(b"%PDF-"):
                                print(f"⚠️ Skipping invalid PDF: {filename}")
                                continue

                        loader = PyPDFLoader(filepath)
                        documents.extend(loader.load())
                    except Exception as e:
                        print(f"❌ Failed to read {filename}: {e}")
                elif filename.endswith('.pptx'):
                    print("📊 Loading PPTX:", filename)
                    from langchain_community.document_loaders import UnstructuredPowerPointLoader
                    loader = UnstructuredPowerPointLoader(filepath)
                    documents.extend(loader.load())

        print(f"📚 Loaded {len(documents)} documents")
        return documents

    def split_documents(self, documents):
        """Split documents into chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✂️  Split into {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, chunks):
        """Create FAISS vector store from chunks"""
        print(" Creating vector store (this may take a few minutes)...")
        
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save to disk
        vectorstore.save_local(self.vectorstore_dir)
        print(f" Vector store saved to {self.vectorstore_dir}/")
        
        return vectorstore
    
    def build(self):
        """Complete pipeline to build vector store"""
        print("\n Starting vector store creation...\n")
        
        documents = self.load_documents()
        
        if not documents:
            print(" No documents found! Please run scraper.py first.")
            return None
        
        chunks = self.split_documents(documents)
        
        vectorstore = self.create_vectorstore(chunks)
        
        print("\n✨ Vector store creation complete!")
        return vectorstore
    
    def load_existing_vectorstore(self):
        """Load existing vector store from disk"""
        if not os.path.exists(self.vectorstore_dir):
            print(" No vector store found. Please build it first.")
            return None
        
        print(" Loading existing vector store...")
        vectorstore = FAISS.load_local(
            self.vectorstore_dir, 
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        print("✅ Vector store loaded!")
        return vectorstore


if __name__ == "__main__":
    builder = VectorStoreBuilder()
    
    # Build vector store
    vectorstore = builder.build()
    
    # Test query
    if vectorstore:
        print("\n🧪 Testing with a sample query...")
        query = "What are the admission requirements?"
        results = vectorstore.similarity_search(query, k=3)
        
        print(f"\nQuery: {query}")
        print("\nTop results:")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"Content preview: {doc.page_content[:200]}...")