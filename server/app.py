"""
app.py
------
FastAPI app for Fake News Detection with BI-LSTM + LIME + RAG explanation.

Flow:
  POST /predict
    1. Clean & preprocess input text
    2. BI-LSTM predicts real / fake + confidence
    3. LIME identifies key words
    4. RAG checks if article is in dataset → explains prediction using
       Qwen + similar articles  (or says it's out of training range)

Run:
    uvicorn app:app --host 127.0.0.1 --port 8000 --reload
"""

import re
import string
import pickle
import os
import numpy as np
import tensorflow as tf

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tensorflow.keras.preprocessing.sequence import pad_sequences
from lime.lime_text import LimeTextExplainer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from dotenv import load_dotenv

from rag_for_py import NewsRAG

load_dotenv()

# ── model config ─────────────────────────────────────────────────────────────

MAX_LEN        = 120
MODEL_PATH     = "model/bilstm_noisy_labels_model.h5"
TOKENIZER_PATH = "model/tokenizer.pkl"
CSV_PATH       = "processed_news.csv"

# ── load model & tokenizer ───────────────────────────────────────────────────

model = tf.keras.models.load_model(MODEL_PATH)

with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)

stop_words = set(stopwords.words("english"))

# ── load RAG (builds FAISS index once at startup) ────────────────────────────

rag = NewsRAG(
    csv_path      = CSV_PATH,
    hf_api_token  = os.getenv("HF_API_TOKEN"),
)

# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(title="Fake News Detection API — BI-LSTM + LIME + RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

# ── helpers (unchanged from original) ────────────────────────────────────────

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\n", " ", text)
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    text = re.sub(r"\W", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stop_words]
    return " ".join(tokens)

def preprocess(text: str):
    cleaned = clean_text(text)
    seq     = tokenizer.texts_to_sequences([cleaned])
    padded  = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")
    return padded

class_names = ["fake", "real"]
explainer   = LimeTextExplainer(class_names=class_names)

def predict_proba_for_lime(texts):
    cleaned = [clean_text(t) for t in texts]
    seq     = tokenizer.texts_to_sequences(cleaned)
    seq     = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")
    probs   = model.predict(seq)
    probs   = np.clip(probs, 1e-7, 1 - 1e-7)
    return np.hstack([1 - probs, probs])

# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Fake News Detection API — BI-LSTM + LIME + RAG is running"}


@app.post("/predict")
def predict(request: TextRequest):
    """
    Full pipeline: BI-LSTM prediction → LIME → RAG explanation.

    Response:
      prediction      — "real" or "fake"
      confidence      — float (probability of real)
      explanation     — LIME word-level scores  [(word, score), ...]
      rag             — {
            status          : "present" | "absent"
            present         : bool
            top_score       : float  (cosine similarity to nearest article)
            response        : str    (the final explanation shown to user)
            similar_articles: [{ text, label, score, subject, date }, ...]
        }
    """
    raw_text = request.text

    # Step 1 — BI-LSTM prediction
    processed = preprocess(raw_text)
    prob      = float(model.predict(processed)[0][0])
    label     = "real" if prob > 0.5 else "fake"
    confidence = prob if label == "real" else 1 - prob

    # Step 2 — LIME explanation
    exp         = explainer.explain_instance(
        raw_text,
        predict_proba_for_lime,
        num_features=10,
        num_samples=1000,
    )
    lime_explanation = exp.as_list()   # [(word, score), ...]

    # Step 3 — RAG: check dataset presence + generate explanation
    rag_result = rag.explain(
        news_text        = raw_text,
        prediction       = label,
        confidence       = confidence,
        lime_explanation = lime_explanation,
    )

    return {
        "prediction":   label,
        "confidence":   round(confidence, 4),
        "explanation":  lime_explanation,
        "rag": {
            "status":           rag_result["status"],
            "present":          rag_result["present"],
            "top_score":        rag_result["top_score"],
            "response":         rag_result["response"],
            "similar_articles": [
                {
                    "text":    a["text"][:300] + "…",
                    "label":   "real" if a["label"] == 1 else "fake",
                    "score":   round(a["score"], 4),
                    "subject": a.get("subject", ""),
                    "date":    a.get("date", ""),
                }
                for a in rag_result["similar_articles"]
            ],
        },
    }


@app.post("/explain")
def explain(request: TextRequest):
    """LIME-only endpoint — unchanged from original."""
    exp = explainer.explain_instance(
        request.text,
        predict_proba_for_lime,
        num_features=10,
        num_samples=500,
    )
    return {"explanation": exp.as_list()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
