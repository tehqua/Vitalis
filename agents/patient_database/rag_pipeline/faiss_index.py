import os
import pickle
import faiss
import numpy as np
import requests
from typing import List, Dict

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "nomic-embed-text"


# EMBEDDING (LOCAL - FREE)

def embed_text(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": text
        }
    )

    if response.status_code != 200:
        raise Exception(response.text)

    data = response.json()

    if "embedding" not in data:
        raise Exception(f"Invalid embedding response: {data}")

    return data["embedding"]


# BUILD INDEX FOR ONE PATIENT

def build_patient_faiss_index(
    patient_id: str,
    documents: List[Dict],
    save_dir: str = "faiss_store"
):
    os.makedirs(save_dir, exist_ok=True)

    vectors = []
    texts = []

    print(f"Embedding {len(documents)} documents...")

    for doc in documents:
        vec = embed_text(doc["text"])
        vectors.append(vec)
        texts.append(doc)

    vectors = np.array(vectors).astype("float32")

    # Normalize for cosine similarity
    faiss.normalize_L2(vectors)

    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)

    # Save index
    index_path = os.path.join(save_dir, f"{patient_id}.index")
    faiss.write_index(index, index_path)

    # Save metadata
    metadata_path = os.path.join(save_dir, f"{patient_id}.pkl")
    with open(metadata_path, "wb") as f:
        pickle.dump(texts, f)

    print(f"Index saved for patient {patient_id}")


# LOAD INDEX

def load_patient_index(patient_id: str, save_dir: str = "faiss_store"):
    index_path = os.path.join(save_dir, f"{patient_id}.index")
    metadata_path = os.path.join(save_dir, f"{patient_id}.pkl")

    if not os.path.exists(index_path):
        raise Exception("Index not found. Build index first.")

    index = faiss.read_index(index_path)

    with open(metadata_path, "rb") as f:
        documents = pickle.load(f)

    return index, documents


# SEARCH

def search_patient(
    patient_id: str,
    query: str,
    k: int = 3,
    save_dir: str = "faiss_store"
):
    index, documents = load_patient_index(patient_id, save_dir)

    query_vec = np.array([embed_text(query)]).astype("float32")
    faiss.normalize_L2(query_vec)

    scores, indices = index.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if idx < len(documents):
            results.append(documents[idx])

    return results