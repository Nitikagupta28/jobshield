"""
train.py
--------
Trains the fake-job classifier and saves it to models/.

Pipeline = TF-IDF (turns text into numbers) -> Logistic Regression (the classifier).
Run:  python ml/train.py
"""
import json
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]


def clean_text(text: str) -> str:
    """Lowercase and keep letters/digits. Keep '@' and '+' out; we handle those in rules.py."""
    text = str(text).lower()
    text = re.sub(r"http\S+", " url ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_text(df: pd.DataFrame) -> pd.Series:
    """Join all text columns of a posting into one string, then clean it."""
    joined = df[TEXT_COLUMNS].fillna("").astype(str).agg(" ".join, axis=1)
    return joined.map(clean_text)


def main():
    df = pd.read_csv(ROOT / "data" / "jobs.csv")
    X = build_text(df)
    y = df["fraudulent"].astype(int)

    # stratify keeps the fake:legit ratio the same in train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000, stop_words="english")),
        # class_weight='balanced' because fake posts are rare; without it the model just says "legit" for everything
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", C=2.0)),
    ])
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(y_test, pred, average="binary")
    metrics = {
        "rows": int(len(df)),
        "fake_share": round(float(y.mean()), 4),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }

    print(classification_report(y_test, pred, target_names=["legit", "fake"]))
    print(json.dumps(metrics, indent=2))

    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(model, ROOT / "models" / "model.joblib")
    (ROOT / "models" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("Saved models/model.joblib and models/metrics.json")


if __name__ == "__main__":
    main()
