import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag_pipeline.pipeline import process_fhir_bundle
from rag_pipeline.faiss_index import build_patient_faiss_index


MEDICAL_RECORD_DIR = "../medical_record"
VECTOR_DB_DIR = "../data/vectordb"


def extract_patient_id(filename: str):
    return filename.replace(".json", "")


def run_batch_embedding(skip_existing=True):
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

    files = list(Path(MEDICAL_RECORD_DIR).glob("*.json"))

    print(f"Found {len(files)} patient files.")
    print("Starting batch embedding...\n")

    success = 0
    failed = 0

    for file_path in files:
        patient_id = extract_patient_id(file_path.name)

        index_file = os.path.join(VECTOR_DB_DIR, f"{patient_id}.index")

        if skip_existing and os.path.exists(index_file):
            print(f"[SKIP] {patient_id} already indexed.")
            continue

        try:
            print(f"[PROCESSING] {patient_id}")

            documents = process_fhir_bundle(str(file_path))

            build_patient_faiss_index(
                patient_id=patient_id,
                documents=documents,
                save_dir=VECTOR_DB_DIR
            )

            print(f"[SUCCESS] {patient_id}\n")
            success += 1

        except Exception as e:
            print(f"[ERROR] {patient_id} -> {str(e)}\n")
            failed += 1

    print("Batch embedding completed.")
    print(f"Success: {success}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    start = datetime.now()
    run_batch_embedding()
    end = datetime.now()
    print(f"Total time: {end - start}")