# rag_hierarchical_index

Simple hierarchical RAG pipeline for querying a PDF with LlamaIndex + Ollama.

## Files

- `embedding.py`: reusable `HierarchicalEmbeddingIndex` class
  - `build_and_save_index(pdf_path)`
  - `load_retriever()`
- `main.py`: CLI entrypoint for retrieval + answer generation

## Run

From project root:

```bash
python main.py --query "What are common causes of stridor in children?"
```

Only `--query` is required. Other arguments have defaults defined at the top of `main.py`.

## Optional flags

```bash
python -m rag_hierarchical_index.main \
  --query "What are warning signs of respiratory distress?" \
  --pdf-path medical_document.pdf \
  --persist-dir ./storage/medical_doc_index \
  --embed-model-name BAAI/bge-large-en-v1.5 \
  --llm-model-name thiagomoraes/medgemma-4b-it:Q4_K_S \
  --similarity-top-k 5 \
  --min-score 0.6 \
  --max-context-nodes 3 \
  --rebuild-index
```

