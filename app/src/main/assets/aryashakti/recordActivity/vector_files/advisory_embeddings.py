import os
import logging
from threading import Lock

import numpy as np

# This service uses only a tokenizer plus ONNX Runtime, not a PyTorch,
# TensorFlow, or Flax model. Suppress Transformers' irrelevant framework notice.
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(os.getcwd(), "recordActivity/vector_files/model.onnx")
TOKENIZER_PATH = os.path.join(BASE_DIR, "local_tokenizer")

_tokenizer = None
_session = None
_load_lock = Lock()
logger = logging.getLogger("recordActivity.embedding_memory")
MEMORY_LOG_PATH = os.path.join(os.getcwd(), "logs", "embedding_memory.log")


def _configure_memory_logger():
    absolute_log_path = os.path.abspath(MEMORY_LOG_PATH)
    if not any(
        isinstance(handler, logging.FileHandler)
        and os.path.abspath(handler.baseFilename) == absolute_log_path
        for handler in logger.handlers
    ):
        os.makedirs(os.path.dirname(absolute_log_path), exist_ok=True)
        file_handler = logging.FileHandler(absolute_log_path)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)


def _rss_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                if line.startswith("VmRSS:"):
                    return round(int(line.split()[1]) / 1024, 1)
    except (FileNotFoundError, OSError, ValueError):
        return None

    return None


def _get_resources():
    global _session, _tokenizer

    if _tokenizer is None or _session is None:
        with _load_lock:
            if _tokenizer is None or _session is None:
                _configure_memory_logger()
                logger.info("Embedding initialization started; rss_mb=%s", _rss_mb())

                import onnxruntime as ort
                from transformers import AutoTokenizer
                logger.info(
                    "Embedding libraries imported; rss_mb=%s", _rss_mb()
                )

                _tokenizer = AutoTokenizer.from_pretrained(
                    TOKENIZER_PATH, local_files_only=True
                )
                logger.info("Tokenizer loaded; rss_mb=%s", _rss_mb())

                _session = ort.InferenceSession(
                    MODEL_PATH, providers=["CPUExecutionProvider"]
                )
                logger.info("ONNX session loaded; rss_mb=%s", _rss_mb())

    return _tokenizer, _session

def embed_text(texts):
    """
    Create embeddings for one or more text inputs using ONNX Runtime.
    """
    if isinstance(texts, str):
        texts = [texts]

    tokenizer, session = _get_resources()

    # Tokenize input
    inputs = tokenizer(texts, return_tensors="np", padding=True, truncation=True)

    # Convert tensors to int64 (required by ONNX)
    ort_inputs = {k: v.astype(np.int64) for k, v in inputs.items()}

    # Run inference
    ort_outputs = session.run(None, ort_inputs)

    # Get embeddings (usually the first output)
    embeddings = ort_outputs[0]

    # Mean pooling across sequence tokens
    pooled = embeddings.mean(axis=1)

    # Return as list of lists
    return pooled.tolist()

# Example usage
if __name__ == "__main__":
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Agriculture and AI can work together to improve sustainability."
    ]

    embs = embed_text(sentences)
    for i, emb in enumerate(embs):
        print(f"Sentence {i+1} embedding length: {len(emb)}")
        print(emb[:10], "...")  # print first 10 values





