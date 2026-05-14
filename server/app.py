import re
import string
import pickle
import os
from pathlib import Path
import numpy as np
import tensorflow as tf

from fastapi import FastAPI
from pydantic import BaseModel
from tensorflow.keras.preprocessing.sequence import pad_sequences
from lime.lime_text import LimeTextExplainer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def env_int(name, default):
    return int(os.getenv(name, str(default)))


def env_float(name, default):
    return float(os.getenv(name, str(default)))


def env_path(name, default):
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else BASE_DIR / value


API_TITLE = os.getenv("API_TITLE", "Fake News Detection API with LIME")
API_READY_MESSAGE = os.getenv(
    "API_READY_MESSAGE",
    "Fake News Detection API with LIME is running",
)
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = env_int("SERVER_PORT", 8000)

MAX_LEN = env_int("MAX_SEQUENCE_LENGTH", 120)
MODEL_PATH = env_path("MODEL_PATH", "model/bilstm_noisy_labels_model.h5")
TOKENIZER_PATH = env_path("TOKENIZER_PATH", "model/tokenizer.pkl")
PREDICTION_THRESHOLD = env_float("PREDICTION_THRESHOLD", 0.5)

LIME_CLASS_NAMES = [
    name.strip()
    for name in os.getenv("LIME_CLASS_NAMES", "fake,real").split(",")
    if name.strip()
]
LIME_PREDICT_NUM_FEATURES = env_int("LIME_PREDICT_NUM_FEATURES", 10)
LIME_PREDICT_NUM_SAMPLES = env_int("LIME_PREDICT_NUM_SAMPLES", 1000)
LIME_EXPLAIN_NUM_FEATURES = env_int("LIME_EXPLAIN_NUM_FEATURES", 10)
LIME_EXPLAIN_NUM_SAMPLES = env_int("LIME_EXPLAIN_NUM_SAMPLES", 500)
STOPWORDS_LANGUAGE = os.getenv("STOPWORDS_LANGUAGE", "english")


model = tf.keras.models.load_model(MODEL_PATH)

with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)

stop_words = set(stopwords.words(STOPWORDS_LANGUAGE))

app = FastAPI(title=API_TITLE)

class TextRequest(BaseModel):
    text: str

def clean_text(text):
    text = text.lower()
    text = re.sub(r"\n", " ", text)
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    text = re.sub(r"\W", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stop_words]

    return " ".join(tokens)

def preprocess(text):
    cleaned = clean_text(text)
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")
    return padded
explainer = LimeTextExplainer(class_names=LIME_CLASS_NAMES)

def predict_proba_for_lime(texts):
    cleaned = [clean_text(t) for t in texts]
    seq = tokenizer.texts_to_sequences(cleaned)
    seq = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")

    probs = model.predict(seq)
    probs = np.clip(probs, 1e-7, 1 - 1e-7)

    return np.hstack([1 - probs, probs])

@app.get("/")
def home():
    return {"message": API_READY_MESSAGE}

@app.post("/predict")
def predict(request: TextRequest):
    processed = preprocess(request.text)

    prob = model.predict(processed)[0][0]
    label = "real" if prob > PREDICTION_THRESHOLD else "fake"

    exp = explainer.explain_instance(
        request.text,
        predict_proba_for_lime,
        num_features=LIME_PREDICT_NUM_FEATURES,
        num_samples=LIME_PREDICT_NUM_SAMPLES,
    )

    explanation = exp.as_list()

    return {
        "prediction": label,
        "confidence": float(prob),
        "explanation": explanation
    }

@app.post("/explain")
def explain(request: TextRequest):
    exp = explainer.explain_instance(
        request.text,
        predict_proba_for_lime,
        num_features=LIME_EXPLAIN_NUM_FEATURES,
        num_samples=LIME_EXPLAIN_NUM_SAMPLES,
    )

    return {
        "explanation": exp.as_list()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
