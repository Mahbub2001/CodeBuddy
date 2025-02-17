import os
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4
from langchain_ollama import OllamaEmbeddings
from pinecone import Pinecone

embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

# Define constants
data_folder = "./data"
chunk_size = 1000
chunk_overlap = 50
check_interval = 10
pinecone_api_key = ""

# Initialize Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Use the existing Pinecone index
index_name = "codebuddy"  # Use your actual index name
index = pc.Index(index_name)  # Connect to existing index

# Ingest a file
def batch_upsert(index, to_upsert, batch_size=100):
    """Splits the data into smaller batches to avoid Pinecone's 4MB limit."""
    for i in range(0, len(to_upsert), batch_size):
        batch = to_upsert[i : i + batch_size]
        index.upsert(vectors=batch)
        print(f"Upserted batch {i//batch_size + 1}/{(len(to_upsert) // batch_size) + 1}")

def ingest_file(file_path):
    if not file_path.lower().endswith('.pdf'):
        print(f"Skipping non-PDF file: {file_path}")
        return
    
    print(f"Starting to ingest file: {file_path}")
    loader = PyPDFLoader(file_path)
    loaded_documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n", " ", ""]
    )
    documents = text_splitter.split_documents(loaded_documents)
    uuids = [str(uuid4()) for _ in range(len(documents))]
    
    print(f"Adding {len(documents)} documents to the vector store")

    # ✅ Corrected embedding call
    embeddings_data = embeddings.embed_documents([doc.page_content for doc in documents])

    # Prepare data for Pinecone
    to_upsert = [
        (uuid, embedding, {'text': doc.page_content}) for uuid, embedding, doc in zip(uuids, embeddings_data, documents)
    ]
    
    # ✅ Use batch processing
    batch_upsert(index, to_upsert, batch_size=50)  # Reduce batch size if needed
    print(f"Finished ingesting file: {file_path}")



# Main loop
def main_loop():
    while True:
        for filename in os.listdir(data_folder):
            if not filename.startswith("_"):
                file_path = os.path.join(data_folder, filename)
                ingest_file(file_path)
                new_filename = "_" + filename
                new_file_path = os.path.join(data_folder, new_filename)
                os.rename(file_path, new_file_path)
        time.sleep(check_interval)  # Check the folder every 10 seconds

# Run the main loop
if __name__ == "__main__":
    main_loop()
