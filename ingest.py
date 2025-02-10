import sqlite3
from sentence_transformers import SentenceTransformer
import pymupdf
import numpy as np


def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    return text


def generate_embeddings(text, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    return model.encode([text])[0].tolist()  


def chunk_text(text, chunk_size=1000, overlap_size=80):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap_size  
    return chunks


def create_db():
    conn = sqlite3.connect("embeddings.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            doc_id TEXT,
            chunk_id INTEGER,
            chunk TEXT,
            embedding BLOB
        )
    ''')
    conn.commit()
    return conn


def embed_pdf(pdf_path, doc_id):
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text)
    conn = create_db()

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    for chunk_id, chunk in enumerate(chunks):
        embedding = generate_embeddings(chunk)
        embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO embeddings (doc_id, chunk_id, chunk, embedding)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, chunk_id, chunk, embedding_blob))
        conn.commit()

    print(f"PDF '{pdf_path}' embedded successfully.")


def search_pdf(query, top_k=3, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    conn = sqlite3.connect("embeddings.db")
    cursor = conn.cursor()

    query_embedding = generate_embeddings(query, model_name)
    query_embedding_array = np.array(query_embedding, dtype=np.float32)

    cursor.execute('''
        SELECT doc_id, chunk_id, chunk, embedding
        FROM embeddings
    ''')

    results = []
    for doc_id, chunk_id, chunk, embedding_blob in cursor.fetchall():
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        similarity = np.dot(query_embedding_array, embedding) / (np.linalg.norm(query_embedding_array) * np.linalg.norm(embedding))
        results.append((similarity, doc_id, chunk_id, chunk))

    results.sort(reverse=True, key=lambda x: x[0])

    return results[:top_k]


pdf_path = "CBook.pdf"
embed_pdf(pdf_path, doc_id="doc_1")

query = "Find information about fork()"
search_results = search_pdf(query)

for score, doc_id, chunk_id, chunk in search_results:
    print(f"Score: {score}\nDoc ID: {doc_id}\nChunk: {chunk}\n")
