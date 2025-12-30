import os
from dotenv import load_dotenv  
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
SQLITE_DB_PATH ="chat_history.db"
FAISS_INDEX_PATH = "faiss_index"

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",  
    model_kwargs={'device': 'cpu'}, 
    encode_kwargs={'normalize_embeddings': True}
)

def initialize_faiss_vector_store():
    # Initialize or load FAISS vector store
    try:
        # Try to load existing index
        if os.path.exists(FAISS_INDEX_PATH):
            print(f"Loading existing FAISS index from {FAISS_INDEX_PATH}")
            vector_store = FAISS.load_local(
                FAISS_INDEX_PATH, 
                embeddings,
                allow_dangerous_deserialization=True  # Required for loading pickled files
            )
            print(f"FAISS index loaded successfully")
        else:
            print("FAISS index not found, need to create a new one with an initial sample document")
        return vector_store
    
    except Exception as e:
        print(f"Error initializing FAISS: {e}")
        raise

def search_result(vector_store, query: str, k: int = 2):
    # Perform similarity search on the FAISS vector store
    if vector_store is None:
        raise ValueError("FAISS vector store is not initialized.")
    
    results = vector_store.similarity_search_with_score(query, k=k)
    if not results:
        return "No relevant information found in the knowledge base."
    source_results=[]

    for i , (doc, score) in enumerate(results,1):
        result_detail={
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
            "source":doc.metadata.get('source'),
            "title":doc.metadata.get('title')
        }
        source_results.append(result_detail)

    print(f"Results:")
    print(f"{'='*100}")
    for i, result in enumerate(source_results, 1):
        print(f"Source: {result['source']}")
        print(f"Title: {result['title']}")
        print(f"Metadata: {result['metadata']}")

    return source_results
