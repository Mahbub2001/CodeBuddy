from sentence_transformers import SentenceTransformer
import chromadb
import fitz 

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    return text

def generate_embeddings(text, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model.encode([text])[0].tolist()  

chroma_client = chromadb.PersistentClient(path="./chroma_db")  
db = chroma_client.get_or_create_collection(name="pdf_embeddings")

def embed_pdf(pdf_path, doc_id):
    text = extract_text_from_pdf(pdf_path)
    embedding = generate_embeddings(text)
    db.add(ids=[doc_id], embeddings=[embedding], documents=[text])
    print(f"PDF '{pdf_path}' embedded successfully.")

def search_pdf(query, top_k=3, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    query_embedding = generate_embeddings(query, model_name)
    results = db.query(query_embeddings=[query_embedding], n_results=top_k)
    return results

pdf_path = "CBook.pdf"  
embed_pdf(pdf_path, doc_id="doc_1")

# testing
query = "Find information about fork()"
search_results = search_pdf(query)
print(search_results)