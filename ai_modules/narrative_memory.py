"""
Narrative Memory Module for SceneSense AI
RAG-style continuity engine for screenplay analysis
"""

import os
import re
from typing import List, Tuple, Any, Optional

try:
    import faiss
except ImportError:
    faiss = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


_EMBEDDER_MODEL = None


def get_embedder():
    """Lazy load the sentence transformer model."""
    global _EMBEDDER_MODEL
    if _EMBEDDER_MODEL is None:
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed.")
        _EMBEDDER_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDER_MODEL


def extract_text_from_pdf(file_obj) -> str:
    """Extracts text from a PDF file object."""
    if PdfReader is None:
        raise ImportError("pypdf not installed.")
    
    reader = PdfReader(file_obj)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text


def chunk_script(text: str, chunk_size_words: int = 300, overlap_words: int = 50) -> List[str]:
    """
    Splits script into overlapping chunks.
    Trying to respect scene boundaries would be ideal, but fixed-window with overlap 
    is robust for retrieval.
    """
    if not text:
        return []
    
    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size_words - overlap_words
    
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size_words]
        chunk_str = " ".join(chunk_words)
        if len(chunk_str) > 50:
            chunks.append(chunk_str)
            
    return chunks


def build_memory_index(chunks: List[str]) -> Tuple[Any, Any]:
    """
    Embeds chunks and builds a FAISS index.
    Returns (index, embeddings_matrix)
    """
    if not chunks:
        return None, None
    if faiss is None or np is None:
        raise ImportError("faiss-cpu or numpy not installed.")

    model = get_embedder()
    embeddings = model.encode(chunks)
    
    embeddings = np.array(embeddings).astype("float32")
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    return index, embeddings


def retrieve_context(query_scene: str, index: Any, chunks: List[str], k: int = 3) -> List[str]:
    """
    Retrieves k most similar chunks to the query_scene.
    """
    if not index or not chunks:
        return []
    if not query_scene.strip():
        return []
        
    model = get_embedder()
    query_emb = model.encode([query_scene])
    query_emb = np.array(query_emb).astype("float32")
    
    distances, indices = index.search(query_emb, k)
    
    results = []
    if indices is not None and len(indices) > 0:
        row = indices[0]
        for idx in row:
            if 0 <= idx < len(chunks):
                results.append(chunks[idx])
                
    return results


def format_context_for_prompt(retrieved_chunks: List[str]) -> str:
    """
    Formats the retrieved chunks into a string for the LLM prompt.
    """
    if not retrieved_chunks:
        return ""
    
    out = "MOVIE NARRATIVE MEMORY (Relevant Context from Full Script):\n"
    out += "=" * 60 + "\n"
    for i, c in enumerate(retrieved_chunks, 1):
        out += f"--- Context Chunk {i} ---\n{c}\n\n"
    out += "=" * 60 + "\n"
    out += "Use this context to maintain narrative consistency.\n"
    return out
