"""
Medical Document RAG Service.

Wraps HierarchicalEmbeddingIndex from rag_hierarchical_index/embedding.py
and exposes a simple retrieve() method for use inside the LangGraph workflow.

Design decisions:
- Singleton pattern: embedding model loaded once, reused across requests.
- Dual timeout:
    - LOAD_TIMEOUT_S  (30s): first-ever call, loads HuggingFace model + LlamaIndex from disk.
    - QUERY_TIMEOUT_S  (8s): subsequent calls, model already warm, only runs inference.
- Graceful fallback: on timeout/error returns None; the reasoning node skips the context.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timeout constants (seconds)
# ---------------------------------------------------------------------------
# First load: includes HuggingFace model download (~1.3 GB for bge-large-en-v1.5)
# + loading the LlamaIndex persisted vector store from disk.
# Set high enough for a first-time download on a typical connection.
# Once cached locally (~/.cache/huggingface), subsequent starts use the fast path.
LOAD_TIMEOUT_S: int = 300  # 5 minutes — covers model download + index load
QUERY_TIMEOUT_S: int = 8   # subsequent queries: model warm, only embedding inference


# ---------------------------------------------------------------------------
# Helper: run a callable in a daemon thread with a hard timeout
# ---------------------------------------------------------------------------
def _run_with_timeout(fn, timeout_s: int):
    """
    Execute `fn()` in a daemon thread.
    Returns (result, None) on success or (None, exception) on timeout/error.
    """
    result_box: list = [None]
    exc_box: list = [None]

    def _target():
        try:
            result_box[0] = fn()
        except Exception as exc:  # noqa: BLE001
            exc_box[0] = exc

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_s)

    if t.is_alive():
        return None, TimeoutError(
            f"Operation exceeded {timeout_s}s timeout"
        )
    if exc_box[0] is not None:
        return None, exc_box[0]
    return result_box[0], None


# ---------------------------------------------------------------------------
# MedicalDocRAGService
# ---------------------------------------------------------------------------
class MedicalDocRAGService:
    """
    Singleton service that wraps HierarchicalEmbeddingIndex.

    Usage::

        svc = MedicalDocRAGService.get_instance(config)
        context_text = svc.retrieve("What are signs of respiratory distress?")
        # context_text is None on failure (graceful fallback)
    """

    _instance: Optional["MedicalDocRAGService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        persist_dir: str,
        embed_model_name: str,
        similarity_top_k: int = 5,
        min_score: float = 0.6,
        max_context_nodes: int = 3,
    ) -> None:
        # Resolve persist_dir relative to the project root (parents[2] of this file).
        # This ensures the path is correct regardless of CWD when the server is started.
        project_root = Path(__file__).parents[2]
        if os.path.isabs(persist_dir):
            self._persist_dir = persist_dir
        else:
            self._persist_dir = str((project_root / persist_dir).resolve())

        self._embed_model_name = embed_model_name
        self._similarity_top_k = similarity_top_k
        self._min_score = min_score
        self._max_context_nodes = max_context_nodes

        # Retriever is loaded lazily on first retrieve() call
        self._retriever = None
        self._is_loaded: bool = False
        self._load_failed: bool = False

    # ------------------------------------------------------------------
    # Singleton factory
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls, config=None) -> "MedicalDocRAGService":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if config is None:
                        raise RuntimeError(
                            "MedicalDocRAGService.get_instance() requires config on first call"
                        )
                    cls._instance = cls(
                        persist_dir=config.medical_doc_persist_dir,
                        embed_model_name=config.medical_doc_embed_model,
                        similarity_top_k=config.medical_doc_similarity_top_k,
                        min_score=config.medical_doc_min_score,
                        max_context_nodes=config.medical_doc_max_context_nodes,
                    )
                    logger.info("MedicalDocRAGService singleton created")
        return cls._instance

    # ------------------------------------------------------------------
    # Internal: lazy load
    # ------------------------------------------------------------------
    def _load_retriever(self) -> None:
        """Load HierarchicalEmbeddingIndex from persisted directory."""
        # Ensure rag_hierarchical_index is importable regardless of CWD
        rag_module_dir = str(
            Path(__file__).parents[2] / "rag_hierarchical_index"
        )
        if rag_module_dir not in sys.path:
            sys.path.insert(0, rag_module_dir)

        # Also ensure project root is in path
        project_root = str(Path(__file__).parents[2])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from embedding import HierarchicalEmbeddingIndex  # noqa: PLC0415

        if not os.path.exists(self._persist_dir):
            raise FileNotFoundError(
                f"Medical doc index not found at: {self._persist_dir}. "
                "Run rag_hierarchical_index/main.py --rebuild-index first."
            )

        index = HierarchicalEmbeddingIndex(
            embed_model_name=self._embed_model_name,
            persist_dir=self._persist_dir,
            similarity_top_k=self._similarity_top_k,
        )
        self._retriever = index.load_retriever()
        self._is_loaded = True
        logger.info(
            "MedicalDocRAGService: retriever loaded from '%s'", self._persist_dir
        )

    # ------------------------------------------------------------------
    # Internal: filter + format retrieved nodes
    # ------------------------------------------------------------------
    def _build_context(self, retrieved_nodes) -> Optional[str]:
        filtered = [
            n for n in retrieved_nodes
            if n.score is not None and n.score > self._min_score
        ]
        top_nodes = sorted(filtered, key=lambda n: n.score, reverse=True)[
            : self._max_context_nodes
        ]

        if not top_nodes:
            logger.info(
                "MedicalDocRAGService: no nodes above min_score=%.2f", self._min_score
            )
            return None

        parts = []
        for i, node in enumerate(top_nodes, start=1):
            page = node.metadata.get("page_label", "?")
            parts.append(
                f"[Doc {i} | score={node.score:.3f} | page={page}]\n{node.text}"
            )

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def retrieve(self, query: str) -> Optional[str]:
        """
        Retrieve relevant medical document context for the given query.

        Returns:
            str: Context text to inject into the LLM prompt.
            None: On timeout, load failure, or low-score results — caller
                  should proceed without this context (graceful fallback).
        """
        if not query or not query.strip():
            return None

        # If we already know loading failed permanently, skip
        if self._load_failed:
            return None

        # --- Lazy load on first call ---
        if not self._is_loaded:
            logger.info(
                "MedicalDocRAGService: first call, loading retriever "
                "(timeout=%ds)...", LOAD_TIMEOUT_S
            )
            t0 = time.monotonic()
            _, err = _run_with_timeout(self._load_retriever, LOAD_TIMEOUT_S)
            elapsed = time.monotonic() - t0

            if err is not None:
                if isinstance(err, TimeoutError):
                    logger.warning(
                        "MedicalDocRAGService: retriever LOAD timed out after %.1fs "
                        "(threshold=%ds). Falling back to LLM-only response.",
                        elapsed, LOAD_TIMEOUT_S
                    )
                else:
                    logger.error(
                        "MedicalDocRAGService: retriever load FAILED: %s. "
                        "Future calls will be skipped.", err, exc_info=True
                    )
                    self._load_failed = True
                return None

            logger.info(
                "MedicalDocRAGService: retriever loaded in %.1fs", elapsed
            )

        # --- Query ---
        logger.info(
            "MedicalDocRAGService: querying (timeout=%ds): '%s'",
            QUERY_TIMEOUT_S, query[:120]
        )
        t0 = time.monotonic()

        def _do_retrieve():
            return self._retriever.retrieve(query)

        nodes, err = _run_with_timeout(_do_retrieve, QUERY_TIMEOUT_S)
        elapsed = time.monotonic() - t0

        if err is not None:
            if isinstance(err, TimeoutError):
                logger.warning(
                    "MedicalDocRAGService: query timed out after %.1fs "
                    "(threshold=%ds). Falling back to LLM-only response.",
                    elapsed, QUERY_TIMEOUT_S
                )
            else:
                logger.error(
                    "MedicalDocRAGService: query error: %s", err, exc_info=True
                )
            return None

        context = self._build_context(nodes)
        if context:
            logger.info(
                "MedicalDocRAGService: retrieved context in %.1fs "
                "(%d chars).", elapsed, len(context)
            )
        return context
