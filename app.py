import re
import string
import pickle
import numpy as np
import tensorflow as tf

from fastapi import FastAPI
from pydantic import BaseModel
from tensorflow.keras.preprocessing.sequence import pad_sequences
from lime.lime_text import LimeTextExplainer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

MAX_LEN = 120 
MODEL_PATH = "model/bilstm_noisy_labels_model.h5"
TOKENIZER_PATH = "model/tokenizer.pkl"


model = tf.keras.models.load_model(MODEL_PATH)

with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)

stop_words = set(stopwords.words("english"))

app = FastAPI(title="Fake News Detection API with LIME")

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
class_names = ["fake", "real"]
explainer = LimeTextExplainer(class_names=class_names)

def predict_proba_for_lime(texts):
    cleaned = [clean_text(t) for t in texts]
    seq = tokenizer.texts_to_sequences(cleaned)
    seq = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")

    probs = model.predict(seq)
    probs = np.clip(probs, 1e-7, 1 - 1e-7)

    return np.hstack([1 - probs, probs])

@app.get("/")
def home():
    return {"message": "🚀 Fake News Detection API with LIME is running"}


@app.post("/predict")
def predict(request: TextRequest):
    processed = preprocess(request.text)

    prob = model.predict(processed)[0][0]
    label = "real" if prob > 0.5 else "fake"

    exp = explainer.explain_instance(
        request.text,
        predict_proba_for_lime,
        num_features=10,
        num_samples=1000  
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
        num_features=10,
        num_samples=500
    )

    return {
        "explanation": exp.as_list()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)