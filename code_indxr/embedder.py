import os
from typing import List, Callable
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global cache for local model
_LOCAL_MODEL = None

def _get_local_model():
    global _LOCAL_MODEL
    if _LOCAL_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _LOCAL_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
        except ImportError:
            raise ImportError(
                "Local embeddings require extra dependencies.\n"
                "Install with: pip install 'code-indexer[local]'"
            )
    return _LOCAL_MODEL

def _local_embed_fn(texts: List[str]) -> List[List[float]]:
    """Embed texts using local BGE-small model."""
    if isinstance(texts, str):
        texts = [texts]
    model = _get_local_model()
    return model.encode(texts, normalize_embeddings=True).tolist()

# Attach required attribute
_local_embed_fn.ndims = 384  # BGE-small dimension
_local_embed_fn.__name__ = "local_bge_small"

def _openai_embed_fn(texts: List[str]) -> List[List[float]]:
    """Embed texts using OpenAI."""
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

_openai_embed_fn.ndims = 1536
_openai_embed_fn.__name__ = "openai_text-embedding-3-small"

def get_embedding_function():
    """Return embedding function: OpenAI if key available, else local."""
    if OPENAI_API_KEY:
        print("✅ Using OpenAI embeddings")
        return _openai_embed_fn
    else:
        print("✅ Using local BGE-small embeddings (offline)")
        return _local_embed_fn