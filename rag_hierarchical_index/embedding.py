import os
from typing import Sequence

from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class HierarchicalEmbeddingIndex:
    """Build and load a hierarchical FAISS-style retriever with LlamaIndex."""

    def __init__(
        self,
        embed_model_name: str,
        persist_dir: str,
        similarity_top_k: int = 5,
        chunk_sizes: Sequence[int] = (1024, 512, 128),
    ) -> None:
        self.embed_model_name = embed_model_name
        self.persist_dir = persist_dir
        self.similarity_top_k = similarity_top_k
        self.chunk_sizes = list(chunk_sizes)

        Settings.embed_model = HuggingFaceEmbedding(model_name=self.embed_model_name)
        Settings.llm = None

    def build_and_save_index(self, pdf_path: str) -> None:
        """Create hierarchical nodes from a PDF and persist the index."""
        documents = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
        node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=self.chunk_sizes)
        nodes = node_parser.get_nodes_from_documents(documents)
        leaf_nodes = get_leaf_nodes(nodes)

        storage_context = StorageContext.from_defaults()
        storage_context.docstore.add_documents(nodes)

        index = VectorStoreIndex(leaf_nodes, storage_context=storage_context)
        os.makedirs(self.persist_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=self.persist_dir)

    def load_retriever(self) -> AutoMergingRetriever:
        """Load persisted index and return an auto-merging retriever."""
        storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
        index = load_index_from_storage(storage_context)
        base_retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
        return AutoMergingRetriever(base_retriever, storage_context, verbose=False)
