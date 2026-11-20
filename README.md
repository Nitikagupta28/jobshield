# JobShield - Fake Job Posting Detector

A full-stack AI/ML web app that tells students and freshers whether a job or internship posting is a scam.
It combines a **machine learning classifier** with a **rule engine** and **explains** why it reached its verdict.

## Run it

```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python ml/make_sample_data.py  # makes data/jobs.csv (skip if you use the real dataset)
python ml/train.py             # trains and saves models/model.joblib
python app.py                  # open http://127.0.0.1:5000
python -m pytest               # run the tests
```

## How it works

```
Browser form --(JSON)--> Flask /api/analyze --> predictor.py
                                                  |-- clean_text()  -> TF-IDF -> Logistic Regression -> ML probability
                                                  |-- rules.py (regex scam patterns)   -> rule score + red flags
                                                  |-- explainability: word contribution = tfidf value x model weight
                                                  '-- hybrid risk = 0.65*ML + 0.35*rules (serious flag forces >= 0.70)
```

| File | Job |
|---|---|
| `ml/make_sample_data.py` | builds a synthetic starter dataset |
| `ml/train.py` | cleans text, trains TF-IDF + Logistic Regression, prints metrics, saves the model |
| `rules.py` | regex rules for fees, ID requests, WhatsApp-only contact, fake earnings |
| `predictor.py` | loads the model once, combines ML + rules, explains the result |
| `app.py` | Flask routes and input validation |
| `templates/`, `static/` | the UI |
| `tests/test_app.py` | automated API and rule tests |

## IMPORTANT: use the real dataset before putting this on your resume

The bundled data is synthetic and templated, so scores of 1.00 are meaningless. Download the
**"Fake Job Postings" (EMSCAD) dataset on Kaggle**, save it as `data/jobs.csv`, and re-run `python ml/train.py`.
It uses the same column names. On real data, expect roughly 0.7-0.85 F1 for the fake class,
and that honest number is what you quote in interviews.

## Upgrade ideas (these are what make it stand out)

1. Real dataset plus a proper evaluation: compare Naive Bayes, Logistic Regression, Linear SVM and Random Forest, and report precision/recall (not just accuracy).
2. Add a "Check company" step: validate the email domain against the company website.
3. Save analyses in SQLite and show a history page and a scam-trend chart.
4. Add a feedback button ("was this correct?") to collect new labelled data.
5. Deploy free on Render or PythonAnywhere and put the live link on your resume.
6. Bonus: a Chrome extension that calls your API from LinkedIn or Naukri pages.

## Resume bullets (edit with your real numbers)

- Built JobShield, a full-stack fake job posting detector using Python, scikit-learn and Flask (TF-IDF + Logistic Regression, F1 = X on the EMSCAD dataset).
- Designed a hybrid ML + rule-based scoring engine with word-level explainability, handling class imbalance via class weighting.
- Developed a REST API with input validation and automated pytest tests; built a responsive JavaScript UI.
