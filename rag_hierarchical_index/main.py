import argparse
import os

from ollama import chat

from embedding import HierarchicalEmbeddingIndex

# ---------- Default Config ----------
EMBED_MODEL_NAME = "BAAI/bge-large-en-v1.5"
LLM_MODEL_NAME = "thiagomoraes/medgemma-4b-it:Q4_K_S"
PDF_PATH = "medical_document.pdf"
PERSIST_DIR = "./large_medical_doc_index"
SIMILARITY_TOP_K = 5
MIN_SCORE = 0.6
MAX_CONTEXT_NODES = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hierarchical RAG query runner (PDF + Ollama)."
    )
    parser.add_argument(
        "--query",
        required=True,
        help="User question to ask against the indexed PDF.",
    )
    parser.add_argument("--embed-model-name", default=EMBED_MODEL_NAME)
    parser.add_argument("--llm-model-name", default=LLM_MODEL_NAME)
    parser.add_argument("--pdf-path", default=PDF_PATH)
    parser.add_argument("--persist-dir", default=PERSIST_DIR)
    parser.add_argument("--similarity-top-k", type=int, default=SIMILARITY_TOP_K)
    parser.add_argument("--min-score", type=float, default=MIN_SCORE)
    parser.add_argument("--max-context-nodes", type=int, default=MAX_CONTEXT_NODES)
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force rebuilding index even if persisted index exists.",
    )
    return parser.parse_args()


def select_context_nodes(retrieved_nodes, min_score: float, max_context_nodes: int):
    filtered = [n for n in retrieved_nodes if (n.score is not None and n.score > min_score)]
    return sorted(filtered, key=lambda n: n.score, reverse=True)[:max_context_nodes]


def build_context_text(context_nodes) -> str:
    if context_nodes:
        return "\n\n".join(f"[Score: {n.score:.4f}]\n{n.text}" for n in context_nodes)
    return "No relevant context found (score threshold not met)."


def answer_with_model(question: str, context_text: str, model_name: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful medical assistant. "
                "Use the provided context to answer. "
                "If context is insufficient, say that clearly. "
                "Do not add any information that is not in the context."
            ),
        },
        {"role": "system", "content": f"RETRIEVED_CONTEXT:\n{context_text}"},
        {"role": "user", "content": question},
    ]

    resp = chat(
        model=model_name,
        messages=messages,
        options={"temperature": 0.3, "num_predict": 512},
    )
    return resp.message.content


def run() -> None:
    args = parse_args()

    index = HierarchicalEmbeddingIndex(
        embed_model_name=args.embed_model_name,
        persist_dir=args.persist_dir,
        similarity_top_k=args.similarity_top_k,
    )

    if args.rebuild_index or not os.path.exists(args.persist_dir):
        index.build_and_save_index(args.pdf_path)
        print(f"Saved index to: {args.persist_dir}")

    retriever = index.load_retriever()
    retrieved_nodes = retriever.retrieve(args.query)
    top_nodes = select_context_nodes(
        retrieved_nodes,
        min_score=args.min_score,
        max_context_nodes=args.max_context_nodes,
    )

    print(f"Selected {len(top_nodes)} node(s) with score > {args.min_score}")
    for i, node in enumerate(top_nodes, start=1):
        print(f"\n--- Context {i} | score={node.score:.4f} ---")
        if "page_label" in node.metadata:
            print("Page:", node.metadata["page_label"])
        print(node.text[:600])

    context_text = build_context_text(top_nodes)
    answer = answer_with_model(args.query, context_text, args.llm_model_name)
    print("\n=== LLM Answer ===")
    print(answer)


if __name__ == "__main__":
    run()
