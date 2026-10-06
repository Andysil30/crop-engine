from fastapi.testclient import TestClient
from backend.main import app
from ml.fertilizer import fertilizer_plan
from ml.train import add_features
import pandas as pd

client = TestClient(app)

RICE = {"N": 90, "P": 42, "K": 43, "temperature": 21,
        "humidity": 82, "ph": 6.5, "rainfall": 203}


def test_home_is_running():
    r =client.get("/health")
    assert r.status_code == 200


def test_predict_returns_three_crops():
    r = client.post("/predict", json=RICE)
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert len(recs) == 3
    assert recs[0]["crop"] == "rice"


def test_confidences_are_sorted_high_to_low():
    recs = client.post("/predict", json=RICE).json()["recommendations"]
    scores = [x["confidence"] for x in recs]
    assert scores == sorted(scores, reverse=True)


def test_bad_ph_is_rejected():
    bad = {**RICE, "ph": 50}
    assert client.post("/predict", json=bad).status_code == 422


def test_missing_field_is_rejected():
    bad = {k: v for k, v in RICE.items() if k != "N"}
    assert client.post("/predict", json=bad).status_code == 422


def test_low_nitrogen_gets_fertilizer_advice():
    plan = fertilizer_plan("rice", N=20, P=47, K=40, ph=6.4)
    n = next(x for x in plan["nutrients"] if x["nutrient"] == "N")
    assert n["status"] == "low"
    assert len(n["products"]) > 0


def test_acidic_soil_gets_lime():
    plan = fertilizer_plan("rice", N=80, P=47, K=40, ph=4.5)
    assert plan["ph"]["advice"] == "add_lime"


def test_feature_engineering_adds_columns():
    row = pd.DataFrame([RICE])
    out = add_features(row)
    assert "water_stress" in out.columns
    assert "NPK_total" in out.columns