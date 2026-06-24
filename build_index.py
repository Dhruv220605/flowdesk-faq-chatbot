"""
Step 2: Build embeddings + FAISS index from FAQ dataset.
Run this once to generate: faiss_index.bin + metadata.json
These get loaded by the Flask backend at query time.
"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ---- Config ----
DATASET_PATH = "faq_dataset.json"
INDEX_OUTPUT_PATH = "faiss_index.bin"
METADATA_OUTPUT_PATH = "metadata.json"
MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, fast, free, runs locally

def load_faq_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_chunk_text(faq_item):
    """
    Combine question + answer into one chunk for embedding.
    Embedding both (not just question) improves retrieval when
    user phrasing doesn't match the question wording exactly.
    """
    return f"Question: {faq_item['question']}\nAnswer: {faq_item['answer']}"

def main():
    print("[1/4] Loading FAQ dataset...")
    faqs = load_faq_dataset(DATASET_PATH)
    print(f"   Loaded {len(faqs)} FAQ pairs.")

    print("[2/4] Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer(MODEL_NAME)

    print("[3/4] Generating embeddings...")
    chunks = [build_chunk_text(item) for item in faqs]
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")

    # Normalize for cosine similarity via inner product
    faiss.normalize_L2(embeddings)

    print("[4/4] Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine sim (since normalized)
    index.add(embeddings)

    faiss.write_index(index, INDEX_OUTPUT_PATH)
    print(f"   Saved FAISS index -> {INDEX_OUTPUT_PATH}")

    # Save metadata so we can map FAISS result index -> original FAQ
    metadata = {
        "model_name": MODEL_NAME,
        "dimension": dimension,
        "faqs": faqs  # same order as embeddings, index i = faqs[i]
    }
    with open(METADATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"   Saved metadata -> {METADATA_OUTPUT_PATH}")

    print("\nDone. Index ready for retrieval in Step 3.")

if __name__ == "__main__":
    main()
