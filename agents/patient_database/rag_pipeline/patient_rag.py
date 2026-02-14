import os
import pickle
import faiss
import numpy as np
import requests
from typing import List, Dict
import re

VECTOR_DB_DIR = "../data/vectordb"

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_EMBED_MODEL = "nomic-embed-text"

# Embedding 
def embed_query(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": OLLAMA_EMBED_MODEL,
            "prompt": text
        }
    )

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()

    if "embedding" not in data:
        raise Exception(f"Invalid embedding response: {data}")

    return data["embedding"] 

# Load Patient Index
def load_patient_index(patient_id: str):
    index_path = os.path.join(VECTOR_DB_DIR, f"{patient_id}.index")
    metadata_path = os.path.join(VECTOR_DB_DIR, f"{patient_id}.pkl")

    if not os.path.exists(index_path):
        raise Exception(f"Index not found for patient {patient_id}")

    index = faiss.read_index(index_path)

    with open(metadata_path, "rb") as f:
        documents = pickle.load(f)

    return index, documents

# Core Retrieval
def extract_year(query: str):
    match = re.search(r"(19|20)\d{2}", query)
    return match.group(0) if match else None

def retrieve_patient_context(patient_id, query, top_k=3):
    index, documents = load_patient_index(patient_id)

    # Structured filter
    year = extract_year(query)
    filtered_docs = documents

    if year:
        filtered_docs = [
            doc for doc in documents
            if doc["metadata"].get("year") == year
        ]

    if len(filtered_docs) == 0:
        filtered_docs = documents

    # Build temporary FAISS index for filtered subset
    vectors = np.array([
        embed_query(doc["text"]) for doc in filtered_docs
    ]).astype("float32")

    faiss.normalize_L2(vectors)

    temp_index = faiss.IndexFlatIP(vectors.shape[1])
    temp_index.add(vectors)

    query_vec = np.array([embed_query(query)]).astype("float32")
    faiss.normalize_L2(query_vec)

    scores, indices = temp_index.search(query_vec, top_k)

    retrieved_docs = [
        filtered_docs[i] for i in indices[0]
        if i < len(filtered_docs)
    ]

    context_text = "\n\n".join([doc["text"] for doc in retrieved_docs])

    return {
        "context": context_text,
        "sources": retrieved_docs
    }

