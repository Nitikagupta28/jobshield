import json
import os
import uuid
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import db
from community import CATEGORIES, apply_community
from extract import classify, extract_entities, mask
from predictor import analyze, get_model

app = Flask(__name__)
# Signs the session cookie. On a real deployment set SECRET_KEY as an environment variable.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.permanent_session_lifetime = timedelta(days=90)
MAX_CHARS = 20000

db.init_db()


def visitor_id() -> str:
    """Give every browser a random id (stored in a signed cookie) to keep their data separate."""
    if "vid" not in session:
        session.permanent = True
        session["vid"] = uuid.uuid4().hex
    return session["vid"]


# ---------------- pages ----------------
@app.get("/")
def home():
    return render_template("index.html")


@app.get("/analyze")
def analyze_page():
    return render_template("analyze.html", categories=CATEGORIES)


@app.get("/history")
def history_page():
    return render_template("history.html", rows=db.get_history(visitor_id()))


@app.post("/history/clear")
def history_clear():
    db.clear_history(visitor_id())
    return redirect(url_for("history_page"))


@app.get("/community")
def community_page():
    top = [{**r, "shown": mask(r["kind"], r["value"]), "day": r["last"][:10]} for r in db.top_reported()]
    return render_template("community.html", stats=db.community_stats(), top=top, categories=CATEGORIES)


@app.get("/guide")
def guide_page():
    return render_template("guide.html")


@app.get("/about")
def about_page():
    return render_template("about.html")


# ---------------- API ----------------
@app.get("/api/health")
def health():
    get_model()
    metrics_file = Path(__file__).parent / "models" / "metrics.json"
    metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else {}
    return jsonify({"status": "ok", "metrics": metrics})


@app.post("/api/analyze")
def analyze_endpoint():
    data = request.get_json(silent=True) or {}
    fields = {k: str(data.get(k, "") or "") for k in
              ("title", "company", "description", "requirements", "benefits")}

    # validation: never trust input from the browser
    if len(fields["description"].strip()) < 20:
        return jsonify({"error": "Please paste the job description (at least 20 characters)."}), 400
    if sum(len(v) for v in fields.values()) > MAX_CHARS:
        return jsonify({"error": "Text is too long."}), 413

    result = analyze(**fields)

    # community layer: find phone numbers / emails / websites and check past reports
    entities = extract_entities(" ".join(fields.values()))
    counts = db.report_counts(entities)
    result["entities"] = [{"kind": k, "value": v, "reports": counts[(k, v)]} for k, v in entities]
    apply_community(result, counts)

    db.save_analysis(
        visitor_id(),
        fields["title"].strip() or "Untitled posting",
        " ".join(fields["description"].split()),
        result,
    )
    return jsonify(result)


@app.post("/api/community/report")
def community_report():
    data = request.get_json(silent=True) or {}
    values = data.get("values")
    category = data.get("category", "other")
    if not isinstance(values, list) or not values or len(values) > 10:
        return jsonify({"error": "Send between 1 and 10 values."}), 400
    if category not in CATEGORIES:
        category = "other"

    entities = []
    for raw in values:
        item = classify(str(raw))      # the server decides what is valid, never the browser
        if item and item not in entities:
            entities.append(item)
    if not entities:
        return jsonify({"error": "Enter a valid phone number, email address or website."}), 400

    added = db.add_reports(visitor_id(), entities, category)
    if added == 0:
        return jsonify({"added": 0, "message": "Nothing new was added. You already reported this, or you reached today's limit."})
    return jsonify({"added": added, "message": f"Thank you. {added} contact{'s' if added != 1 else ''} reported."})


@app.get("/api/community/check")
def community_check():
    item = classify(request.args.get("q", ""))
    if not item:
        return jsonify({"error": "Enter a valid phone number, email address or website."}), 400
    kind, value = item
    cats = db.report_categories(kind, value)
    return jsonify({
        "kind": kind,
        "value": value,
        "reports": sum(cats.values()),
        "categories": [{"label": CATEGORIES.get(c, "Other scam"), "count": n} for c, n in cats.items()],
    })


if __name__ == "__main__":
    app.run(debug=True)