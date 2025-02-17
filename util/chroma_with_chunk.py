from sentence_transformers import SentenceTransformer
import chromadb
import pymupdf  # PyMuPDF
import os

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
db = chroma_client.get_or_create_collection(name="pdf_embeddings")

# Load Sentence Transformer model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def extract_text_from_pdf(pdf_path, chunk_size=1000, overlap=800):
    """Extracts text from a PDF and splits it into chunks."""
    try:
        doc = pymupdf.open(pdf_path)
        full_text = "\n".join(page.get_text() for page in doc)
        
        # Debug: Print the first 500 characters of the extracted text
        print("Extracted text (first 500 chars):", full_text[:500])
        
        # Split text into overlapping chunks
        chunks = []
        start = 0
        while start < len(full_text):
            end = start + chunk_size
            chunk = full_text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap  # Create overlapping chunks
        
        return chunks
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []

def embed_pdf(pdf_path, doc_id):
    """Extracts text, splits into chunks, embeds, and stores in ChromaDB."""
    # Step 1: Extract text and split into chunks
    chunks = extract_text_from_pdf(pdf_path)
    if not chunks:
        print("No text extracted from PDF. Exiting.")
        return
    
    # Step 2: Generate embeddings
    embeddings = [model.encode(chunk).tolist() for chunk in chunks]
    
    # Debug: Print the shape of the first embedding
    print(f"Shape of first embedding: {len(embeddings[0])}")
    
    # Step 3: Store each chunk as a separate entry in the database
    doc_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    db.add(ids=doc_ids, embeddings=embeddings, documents=chunks)
    print(f"PDF '{pdf_path}' embedded successfully with {len(chunks)} chunks.")
    
    # Debug: Verify the collection count
    print(f"Collection count: {db.count()}")

def search_pdf(query, top_k=3):
    """Searches the embedded PDF chunks using semantic similarity."""
    try:
        query_embedding = model.encode(query).tolist()
        results = db.query(query_embeddings=[query_embedding], n_results=top_k)
        
        # Debug: Print the results
        print("Query results:", results)
        
        # Extract relevant chunks
        retrieved_chunks = results.get("documents", [[]])[0]
        return retrieved_chunks
    except Exception as e:
        print(f"Error searching PDF: {e}")
        return []

# Usage
pdf_path = "/kaggle/input/embed-book/CBook.pdf"

# Step 1: Verify PDF path
if not os.path.exists(pdf_path):
    print(f"PDF file not found at path: {pdf_path}")
else:
    # Step 2: Embed the PDF
    embed_pdf(pdf_path, doc_id="doc_1")
    
    # Step 3: Test the search function
    query = "Find information about fork()"
    search_results = search_pdf(query)
    
    # Print search results
    if search_results:
        print("\nSearch Results:")
        for i, chunk in enumerate(search_results):
            print(f"\nChunk {i+1}:\n{chunk}")
    else:
        print("No search results found.")