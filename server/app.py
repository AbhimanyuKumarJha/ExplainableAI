"""
app.py
------
FastAPI app for Fake News Detection with BI-LSTM + LIME + RAG explanation.

Flow:
  POST /predict
    1. Clean & preprocess input text
    2. BI-LSTM predicts real / fake + confidence
    3. LIME identifies key words
    4. RAG checks if article is in dataset → model 0/1 →label → explains prediction using
       Qwen + similar articles  (or says it's out of training range) show real/fake +

Run:
    uvicorn app:app --host 127.0.0.1 --port 8000 --reload
"""

import re
import string
import pickle
import os
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tensorflow.keras.preprocessing.sequence import pad_sequences

from lime.lime_text import LimeTextExplainer

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from dotenv import load_dotenv

from rag_for_py import NewsRAG

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger(__name__)

# ── model config ─────────────────────────────────────────────────────────────

MAX_LEN        = 120
MODEL_PATH     = BASE_DIR / "model" / "bilstm_noisy_labels_model.h5"
TOKENIZER_PATH = BASE_DIR / "model" / "tokenizer.pkl"
CSV_PATH       = BASE_DIR / "processed_news.csv"

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

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.ngrok-free\.dev",
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )

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

def fallback_rag_response(error_message: str):
    return {
        "status": "unavailable",
        "present": False,
        "top_score": 0.0,
        "response": (
            "RAG evidence could not be generated for this request. "
            "The classifier and LIME result are still returned."
        ),
        "similar_articles": [],
        "error": error_message,
    }

def serialize_rag_article(article):
    article_label = article.get("label")
    label = article_label if article_label in ("real", "fake") else (
        "real" if article_label == 1 else "fake"
    )

    return {
        "text": f"{article.get('text', '')[:300]}...",
        "label": label,
        "score": round(float(article.get("score", 0)), 4),
        "subject": article.get("subject", ""),
        "date": article.get("date", ""),
    }

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
    try:
        processed = preprocess(raw_text)
        prob      = float(model.predict(processed)[0][0])
        label     = "real" if prob > 0.5 else "fake"
        confidence = prob if label == "real" else 1 - prob
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        ) from exc

    # Step 2 — LIME explanation
    try:
        exp         = explainer.explain_instance(
            raw_text,
            predict_proba_for_lime,
            num_features=10,
            num_samples=1000,
        )
        lime_explanation = exp.as_list()   # [(word, score), ...]
    except Exception as exc:
        logger.exception("LIME explanation failed")
        lime_explanation = []

    # Step 3 — RAG: check dataset presence + generate explanation
    try:
        rag_result = rag.explain(
            news_text        = raw_text,
            prediction       = label,
            confidence       = confidence,
            lime_explanation = lime_explanation,
        )
    except Exception as exc:
        logger.exception("RAG explanation failed")
        rag_result = fallback_rag_response(str(exc))

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
                serialize_rag_article(a)
                for a in rag_result.get("similar_articles", [])
            ],
            "error":            rag_result.get("error"),
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
