import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

FAISS_INDEX_PATH = "faiss_index"
vector_store = None
embeddings = None

def initialize_vector_store():
    # Initialize or load the FAISS vector store
    global vector_store, embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2",  model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True}
)
    try:
        if os.path.exists(FAISS_INDEX_PATH):
            vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("Loaded existing FAISS index")
        else:
            init_doc=Document(page_content="This is the initial document to create the FAISS index.", metadata={})
            vector_store = FAISS.from_documents([init_doc], embeddings)
            vector_store.save_local(FAISS_INDEX_PATH)
            print("Created new FAISS index")
    except Exception as e:
        print(f"Error initializing FAISS: {e}")
        raise


def add_documents_to_faiss(documents: list[Document]):
    # Add new documents to the FAISS index and save it
    global vector_store
    vector_store.add_documents(documents)
    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"Added {len(documents)} documents to FAISS index")
2
def add_from_pdf(pdf_path: str):
    """Add documents from a PDF file."""
    print(f"\n=== Adding Documents from PDF: {pdf_path} ===")
    
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_docs = text_splitter.split_documents(documents)

        for doc in split_docs:
            doc.metadata["file_type"] = "pdf"
            doc.metadata["source"] = str(os.path.getctime(pdf_path))
        
        add_documents_to_faiss(split_docs)
        print(f"Added {len(split_docs)} chunks from PDF ({len(documents)} pages)")
        
    except Exception as e:
        print(f"{e}")

def add_from_directory(directory_path: str, file_type: str = "*.txt"):
    # Add all documents from a directory
    print(f"\n Adding Documents from Directory: {directory_path} ===")
    
    try:
        loader = DirectoryLoader(directory_path, glob=file_type, loader_cls=PyPDFLoader, use_multithreading=False)
        documents = loader.load()
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        split_docs = text_splitter.split_documents(documents)
        for doc in split_docs:
            doc.metadata["file_type"] = "pdf"
            doc.metadata["source"] = str(os.path.dirname(doc.metadata.get("source", "")))
        
        add_documents_to_faiss(split_docs)
        print(f"Added {len(split_docs)} chunks from {len(documents)} files")
        
    except Exception as e:
        print(f"Error loading directory: {e}")

def interactive_mode():
    # Interactive mode to add documents
    print("\n" + "="*70)
    print("=== Interactive Document Addition ===")
    print("="*70)
    
    while True:
        print("\nOptions:")
        print("  1. Add from PDF file")
        print("  2. Add from directory")
        print("  3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice == "1":
            pdf_path = input("Enter PDF file path: ").strip()
            if os.path.exists(pdf_path):
                add_from_pdf(pdf_path)
            else:
                print("File not found")
        elif choice == "2":
            dir_path = input("Enter directory path: ").strip()
            if os.path.exists(dir_path):
                add_from_directory(dir_path, file_type="*.pdf" )
            else:
                print("Directory not found")
        elif choice == "3":
            print("\n End!")
            break
        else:
            print("Invalid choice")

def main():
    print("\n" + "="*70)
    print("   FAISS Vector Store - Document Addition Utility")
    print("="*70)
    print("\nThis utility helps you add documents to your FAISS vector store.")
    print("Current vector store location: faiss_index/")

    initialize_vector_store()
    interactive_mode()

if __name__ == "__main__":   

    main()
