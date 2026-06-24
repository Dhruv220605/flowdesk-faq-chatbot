"""
Step 3: RAG backend for FlowDesk FAQ chatbot.
Flow: user query -> embed -> FAISS retrieve top-k -> build grounded prompt
      -> Gemini generates answer -> log query + confidence -> return response.
"""

import os
import json
import sqlite3
import datetime

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from google import genai
from flask import Flask, request, jsonify
from flask_cors import CORS

# ---- Config ----
INDEX_PATH = "faiss_index.bin"
METADATA_PATH = "metadata.json"
DB_PATH = "chat_logs.db"
TOP_K = 3
LOW_CONFIDENCE_THRESHOLD = 0.45  # below this, treat as "unanswered" for log

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")  # check ai.google.dev for current model names

if not GEMINI_API_KEY:
    raise RuntimeError("Set GEMINI_API_KEY environment variable before running.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")  # set to your Vercel URL in production
CORS(app, origins=[FRONTEND_URL] if FRONTEND_URL != "*" else "*")

# ---- Load embedding model + FAISS index + metadata at startup ----
print("Loading embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Loading FAISS index + metadata...")
index = faiss.read_index(INDEX_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)
faqs = metadata["faqs"]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            answer TEXT,
            top_score REAL,
            is_low_confidence INTEGER,
            helpful INTEGER DEFAULT NULL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def retrieve(query, top_k=TOP_K):
    query_vec = embed_model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append({"faq": faqs[idx], "score": float(score)})
    return results


def build_prompt(query, retrieved):
    context_blocks = []
    for r in retrieved:
        faq = r["faq"]
        context_blocks.append(f"Q: {faq['question']}\nA: {faq['answer']}")
    context = "\n\n".join(context_blocks)

    prompt = f"""You are FlowDesk's support assistant. Answer the user's question using ONLY the context below.
If the context does not contain enough information to answer, say:
"I don't have information on that yet — please contact support@flowdesk.io."
Do not make up features, prices, or policies not present in the context.

Context:
{context}

User question: {query}

Answer concisely in 2-3 sentences:"""
    return prompt


def log_interaction(query, answer, top_score, is_low_confidence):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO chat_logs (query, answer, top_score, is_low_confidence, timestamp) VALUES (?, ?, ?, ?, ?)",
        (query, answer, top_score, int(is_low_confidence), datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    log_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return log_id


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("message", "").strip()
    if not query:
        return jsonify({"error": "Empty message"}), 400

    retrieved = retrieve(query)
    top_score = retrieved[0]["score"] if retrieved else 0.0
    is_low_confidence = top_score < LOW_CONFIDENCE_THRESHOLD

    prompt = build_prompt(query, retrieved)
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt
    )
    answer = response.text.strip()

    log_id = log_interaction(query, answer, top_score, is_low_confidence)

    sources = [r["faq"]["question"] for r in retrieved]

    return jsonify({
        "log_id": log_id,
        "answer": answer,
        "confidence": round(top_score, 3),
        "low_confidence": is_low_confidence,
        "sources": sources
    })


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    log_id = data.get("log_id")
    helpful = data.get("helpful")  # true/false

    if log_id is None or helpful is None:
        return jsonify({"error": "log_id and helpful required"}), 400

    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE chat_logs SET helpful = ? WHERE id = ?", (int(helpful), log_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "faqs_loaded": len(faqs)})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000, use_reloader=False)