"""
predictor.py
------------
Loads the trained model and turns raw posting text into a full risk report:
ML probability + rule flags + suspicious words (explainability) + final verdict.
"""
from pathlib import Path

import joblib
import numpy as np

from ml.train import clean_text
from rules import run_rules

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "model.joblib"

ML_WEIGHT = 0.65   # how much we trust the ML model
RULE_WEIGHT = 0.35  # how much we trust the rule engine

_model = None


def get_model():
    """Load the model once and reuse it (loading from disk on every request is slow)."""
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("Model not found. Run: python ml/train.py")
        _model = joblib.load(MODEL_PATH)
    return _model


def top_suspicious_words(model, cleaned: str, k: int = 8):
    """
    Explainability: which words pushed the score towards 'fake'?
    contribution of a word = its TF-IDF value in this text * its weight in logistic regression.
    Positive contribution -> pushes towards fake.
    """
    tfidf = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    vec = tfidf.transform([cleaned])
    if vec.nnz == 0:
        return []
    contrib = vec.multiply(clf.coef_[0]).tocsr()
    names = tfidf.get_feature_names_out()
    idx = contrib.indices
    vals = contrib.data
    order = np.argsort(vals)[::-1][:k]
    return [{"word": names[idx[i]], "impact": round(float(vals[i]), 4)} for i in order if vals[i] > 0]


def verdict_for(score: float):
    if score >= 0.65:
        return "High risk", "danger"
    if score >= 0.35:
        return "Suspicious", "warning"
    return "Looks safe", "safe"


def analyze(title="", company="", description="", requirements="", benefits=""):
    model = get_model()
    # Same column order as training: title, company_profile, description, requirements, benefits
    raw = " ".join([title, company, description, requirements, benefits])
    cleaned = clean_text(raw)

    ml_prob = float(model.predict_proba([cleaned])[0, 1])
    flags, rule_score = run_rules(raw)

    # Hybrid score. A very serious rule (like asking for money) should never be hidden by a low ML score.
    risk = ML_WEIGHT * ml_prob + RULE_WEIGHT * rule_score
    if any(f["weight"] >= 0.8 for f in flags):
        risk = max(risk, 0.7)
    risk = round(min(risk, 1.0), 4)

    label, level = verdict_for(risk)
    return {
        "risk_score": risk,
        "risk_percent": round(risk * 100),
        "verdict": label,
        "level": level,
        "ml_probability": round(ml_prob, 4),
        "rule_score": rule_score,
        "red_flags": flags,
        "suspicious_words": top_suspicious_words(model, cleaned),
    }
