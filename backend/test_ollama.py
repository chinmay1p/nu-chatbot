from langchain_community.llms import Ollama

def test_ollama():
    try:
        llm = Ollama(model="llama3", temperature=0.3)
        
        prompt = "Hello! Can you give me a short introduction about Nirma University?"
        print("Sending prompt to LLM...")
        
        response = llm(prompt)
        print("\n✅ Response from LLM:")
        print(response)
        
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    test_ollama()
