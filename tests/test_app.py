import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app import app
from rules import run_rules


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_home_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"JobShield" in r.data


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_scam_is_high_risk(client):
    r = client.post("/api/analyze", json={
        "title": "Online Typing Job",
        "description": "Pay registration fee of Rs 999 to confirm your seat. Contact on WhatsApp. Earn Rs 50000 weekly!!!",
    })
    body = r.get_json()
    assert r.status_code == 200
    assert body["level"] == "danger"
    assert any(f["name"] == "Asks for money" for f in body["red_flags"])


def test_genuine_is_safe(client):
    r = client.post("/api/analyze", json={
        "title": "Data Analyst",
        "company": "Finlytics builds analytics software for banks.",
        "description": "You will analyse business data, build dashboards and present insights to stakeholders each month.",
        "requirements": "BCA or B.Tech with SQL knowledge.",
    })
    assert r.get_json()["level"] == "safe"


def test_short_description_rejected(client):
    r = client.post("/api/analyze", json={"description": "hi"})
    assert r.status_code == 400


def test_empty_body_rejected(client):
    r = client.post("/api/analyze", data="not json", content_type="text/plain")
    assert r.status_code == 400


def test_rules_personal_email():
    flags, score = run_rules("Send CV to jobs@gmail.com")
    assert any(f["name"] == "Personal email domain" for f in flags)
    assert 0 < score < 1
