"""
rag.py
------
RAG system for the XAI Fake News Detection project.

Three-step logic:
  Step 1 — Check if the input news exists in the dataset
            (cosine similarity >= MATCH_THRESHOLD → present, else absent)

  Step 2 — If PRESENT: find the closest matching articles, then use
            Qwen to explain WHY the BI-LSTM model predicted real/fake,
            grounding the explanation in those similar articles.
            2-3 lines for real, 5-6 lines for fake.

  Step 3 — If ABSENT: return a short message saying the news is outside
            the dataset's training period (April 2015 – September 2017).

Stack:
  • sentence-transformers/all-MiniLM-L6-v2  →  dense embeddings
  • FAISS IndexFlatIP                        →  cosine similarity search
  • Qwen/Qwen1.5-7B-Chat (HF Inference API) →  natural language explanation

Usage:
    from rag import NewsRAG
    rag = NewsRAG(csv_path="processed_news.csv")

    result = rag.explain(
        news_text="Trump signed the executive order...",
        prediction="fake",          # from your BI-LSTM / app.py
        confidence=0.87,            # from app.py
        lime_explanation=[...]      # from app.py  (list of (word, score))
    )
    print(result["response"])
"""

from __future__ import annotations

import os
import logging
import numpy as np
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── constants ────────────────────────────────────────────────────────────────

EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM     = 384

# Cosine similarity threshold to decide "present in dataset"
# all-MiniLM scores: >0.85 = near-duplicate, 0.70-0.85 = closely related
MATCH_THRESHOLD = 0.75

# How many similar articles to retrieve for the explanation context
TOP_K_SIMILAR = 3

# Dataset date range (used in the "not present" message)
DATASET_START = "April 2015"
DATASET_END   = "September 2017"

# HuggingFace Inference API — Qwen primary, Mistral fallback
QWEN_URL     = "https://api-inference.huggingface.co/models/Qwen/Qwen1.5-7B-Chat"
FALLBACK_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"


# ── NewsRAG ──────────────────────────────────────────────────────────────────

class NewsRAG:
    """
    Load the dataset once, build a FAISS index, then answer explain() calls.
    """

    def __init__(
        self,
        csv_path: str = "processed_news.csv",
        hf_api_token: str | None = None,
        match_threshold: float = MATCH_THRESHOLD,
    ):
        self.hf_api_token   = hf_api_token or os.getenv("HF_API_TOKEN", "")
        self.match_threshold = match_threshold

        self._encoder = None
        self._index   = None
        self._df      = None

        log.info("Loading dataset …")
        self._load_dataset(csv_path)

        log.info("Building FAISS index …")
        self._build_index()

    # ── setup ─────────────────────────────────────────────────────────────────

    def _load_dataset(self, csv_path: str) -> None:
        df = pd.read_csv(csv_path)
        # Keep only rows with actual text
        df = df[df["text"].notna() & (df["text"].str.strip() != "")].reset_index(drop=True)
        self._df = df
        log.info(f"Dataset loaded: {len(df)} rows  (fake={sum(df['label']==0)}, real={sum(df['label']==1)})")

    def _build_index(self) -> None:
        from sentence_transformers import SentenceTransformer
        import faiss

        log.info(f"Loading embedding model: {EMBED_MODEL}")
        self._encoder = SentenceTransformer(EMBED_MODEL)

        texts = self._df["text"].tolist()
        log.info(f"Embedding {len(texts)} articles (this takes a minute on first run) …")

        embeddings = self._encoder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine via inner product
            show_progress_bar=True,
            batch_size=256,
        )

        self._index = faiss.IndexFlatIP(EMBED_DIM)
        self._index.add(embeddings.astype(np.float32))
        log.info(f"FAISS index ready — {self._index.ntotal} vectors.")

    # ── core search ──────────────────────────────────────────────────────────

    def _embed_query(self, text: str) -> np.ndarray:
        vec = self._encoder.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vec.astype(np.float32)

    def _search(self, query_vec: np.ndarray, top_k: int = TOP_K_SIMILAR + 1):
        scores, indices = self._index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            row = self._df.iloc[idx]
            results.append({
                "score":   float(score),
                "text":    row["text"],
                "label":   int(row["label"]),
                "subject": row.get("subject", ""),
                "date":    row.get("date", ""),
                "idx":     int(idx),
            })
        return results

    # ── Qwen generation ───────────────────────────────────────────────────────

    def _call_llm(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.hf_api_token:
            headers["Authorization"] = f"Bearer {self.hf_api_token}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.3,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }

        for url in [QWEN_URL, FALLBACK_URL]:
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0].get("generated_text", "").strip()
                if isinstance(data, dict):
                    return data.get("generated_text", "").strip()
            except Exception as e:
                log.warning(f"LLM call to {url} failed: {e}")
                continue

        return None   # both endpoints failed

    def _build_prompt(
        self,
        news_text: str,
        prediction: str,
        confidence: float,
        lime_explanation: list,
        similar_articles: list,
    ) -> str:
        """
        Build a Qwen chat-format prompt.
        - fake  → 5-6 sentence explanation
        - real  → 2-3 sentence explanation
        """
        length_instruction = (
            "Write a detailed explanation of 5 to 6 sentences."
            if prediction == "fake"
            else "Write a concise explanation of 2 to 3 sentences."
        )

        # Format LIME top words
        if lime_explanation:
            top_words = sorted(lime_explanation, key=lambda x: abs(x[1]), reverse=True)[:5]
            lime_str = ", ".join(
                f"'{w}' ({'supports fake' if s < 0 else 'supports real'})"
                for w, s in top_words
            )
        else:
            lime_str = "not available"

        # Format similar articles context
        ctx_parts = []
        for i, art in enumerate(similar_articles[:TOP_K_SIMILAR], 1):
            label_word = "REAL" if art["label"] == 1 else "FAKE"
            ctx_parts.append(
                f"[Similar article {i} — labelled {label_word}, similarity {art['score']:.2f}]\n"
                f"{art['text'][:300]}…"
            )
        context_str = "\n\n".join(ctx_parts)

        prompt = (
            "<|im_start|>system\n"
            "You are an expert AI assistant for a fake news detection system. "
            "Your job is to explain, in plain English, why a news article was "
            "classified as real or fake by a BI-LSTM deep learning model. "
            "Base your explanation on: the article text, the LIME word-level "
            "importance scores, and the most similar articles found in the dataset. "
            "Do not make up facts. Be specific about the linguistic signals.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"The model classified the following news article as **{prediction.upper()}** "
            f"with {confidence*100:.1f}% confidence.\n\n"
            f"=== INPUT ARTICLE ===\n{news_text[:500]}{'…' if len(news_text) > 500 else ''}\n\n"
            f"=== LIME KEY WORDS ===\n{lime_str}\n\n"
            f"=== MOST SIMILAR ARTICLES IN DATASET ===\n{context_str}\n\n"
            f"Explain clearly why this article was predicted as {prediction}. "
            f"{length_instruction} "
            f"Reference specific words or phrases from the article and the similar articles.\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        return prompt

    def _fallback_explanation(
        self,
        news_text: str,
        prediction: str,
        confidence: float,
        lime_explanation: list,
        similar_articles: list,
    ) -> str:
        """
        Extractive explanation when the LLM is unreachable.
        Uses LIME words and similar article labels to compose a rule-based response.
        """
        if lime_explanation:
            top = sorted(lime_explanation, key=lambda x: abs(x[1]), reverse=True)[:3]
            word_list = ", ".join(f"'{w}'" for w, _ in top)
        else:
            word_list = "several key terms"

        sim_labels = [a["label"] for a in similar_articles]
        fake_count = sim_labels.count(0)
        real_count = sim_labels.count(1)

        if prediction == "fake":
            return (
                f"The model classified this article as FAKE with {confidence*100:.1f}% confidence. "
                f"The LIME analysis highlights {word_list} as the most influential words driving this prediction. "
                f"Among the {len(similar_articles)} most similar articles found in the training dataset, "
                f"{fake_count} were labelled fake and {real_count} were labelled real, "
                f"indicating this article shares linguistic patterns commonly associated with fake news. "
                f"The writing style, word choice, and rhetorical structure of this article are consistent "
                f"with manipulative or misleading content the model was trained to detect."
            )
        else:
            return (
                f"The model classified this article as REAL with {confidence*100:.1f}% confidence. "
                f"The LIME analysis identifies {word_list} as key indicators supporting this prediction. "
                f"Among the {len(similar_articles)} most similar articles in the dataset, "
                f"{real_count} were labelled real, suggesting strong alignment with verified news patterns."
            )

    # ── public API ────────────────────────────────────────────────────────────

    def explain(
        self,
        news_text: str,
        prediction: str,
        confidence: float,
        lime_explanation: list | None = None,
    ) -> dict:
        """
        Main entry point. Called after app.py has already run the BI-LSTM
        and LIME and has a prediction + explanation ready.

        Args:
            news_text       — raw or cleaned news text
            prediction      — "fake" or "real"  (from app.py)
            confidence      — float 0-1          (from app.py)
            lime_explanation— list of (word, score) tuples (from app.py)

        Returns dict with keys:
            present         — True if news found in dataset, False if not
            top_score       — highest cosine similarity found
            similar_articles— list of closest matches (dicts)
            response        — the final text to show the user
            status          — "present" | "absent"
        """
        if lime_explanation is None:
            lime_explanation = []

        # ── Step 1: search dataset ────────────────────────────────────────────
        query_vec      = self._embed_query(news_text)
        search_results = self._search(query_vec, top_k=TOP_K_SIMILAR + 1)

        top_score = search_results[0]["score"] if search_results else 0.0
        present   = top_score >= self.match_threshold

        # ── Step 2 & 3: build response ────────────────────────────────────────
        if not present:
            # Step 3 — not in dataset
            response = (
                f"This news article was not found in the dataset the model was trained on. "
                f"The training data covers news from {DATASET_START} to {DATASET_END}. "
                f"If this article is from outside that period, the model's prediction may not be reliable."
            )
            status = "absent"

        else:
            # Step 2 — present: generate explanation with Qwen
            similar = search_results[:TOP_K_SIMILAR]

            prompt = self._build_prompt(
                news_text        = news_text,
                prediction       = prediction,
                confidence       = confidence,
                lime_explanation = lime_explanation,
                similar_articles = similar,
            )

            llm_output = self._call_llm(prompt)

            if llm_output:
                response = llm_output
            else:
                # Fallback if LLM is unavailable
                response = self._fallback_explanation(
                    news_text, prediction, confidence, lime_explanation, similar
                )

            status = "present"

        return {
            "present":          present,
            "top_score":        round(top_score, 4),
            "similar_articles": search_results[:TOP_K_SIMILAR],
            "response":         response,
            "status":           status,
        }
