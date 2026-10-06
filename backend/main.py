from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.train import add_features
from ml.fertilizer import fertilizer_plan
from backend.weather import get_weather, WeatherError
from backend.db import SessionLocal, Prediction, init_db

ROOT = Path(__file__).resolve().parent.parent

# Load the trained brain once, when the server starts
model = joblib.load(ROOT / "models" / "model.pkl")
le = joblib.load(ROOT / "models" / "label_encoder.pkl")
features = joblib.load(ROOT / "models" / "features.pkl")

app = FastAPI(title="Smart Crop & Fertilizer Engine")

# Create the database table if it doesn't exist yet
try:
    init_db()
except Exception as e:
    print("DATABASE PROBLEM AT STARTUP:", e)

# Lets our web page (frontend) talk to this server
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class SoilInput(BaseModel):
    N: float = Field(ge=0, le=200)
    P: float = Field(ge=0, le=200)
    K: float = Field(ge=0, le=300)
    temperature: float = Field(ge=-10, le=50)
    humidity: float = Field(ge=0, le=100)
    ph: float = Field(ge=0, le=14)
    rainfall: float = Field(ge=0, le=400)


@app.get("/health")
def home():
    return {"message": "Crop engine is running"}


@app.post("/predict")
def predict(inp: SoilInput):
    row = pd.DataFrame([inp.model_dump()])
    X = add_features(row)[features]          # same recipe as training
    probs = model.predict_proba(X)[0]
    top3 = np.argsort(probs)[-3:][::-1]      # 3 highest scores

    results = []
    for i in top3:
        crop = str(le.classes_[i])
        results.append({
            "crop": crop,
            "confidence": round(float(probs[i]) * 100, 1),
            "fertilizer": fertilizer_plan(crop, inp.N, inp.P, inp.K, inp.ph),
        })

    # Write this prediction into the database notebook
    try:
        with SessionLocal() as session:
            session.add(Prediction(
                **inp.model_dump(),
                top_crop=results[0]["crop"],
                results=results,
            ))
            session.commit()
    except Exception as e:
        print("Could not save to database:", e)   # don't crash the farmer's answer

    return {"recommendations": results}


@app.get("/weather")
def weather(city: str):
    try:
        return get_weather(city)
    except WeatherError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/history")
def history(limit: int = 20):
    with SessionLocal() as session:
        rows = (session.query(Prediction)
                .order_by(Prediction.created_at.desc())
                .limit(limit).all())
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "inputs": {"N": r.N, "P": r.P, "K": r.K, "temperature": r.temperature,
                           "humidity": r.humidity, "ph": r.ph, "rainfall": r.rainfall},
                "top_crop": r.top_crop,
            }
            for r in rows
        ]
    # Serve the farmer's web page from the same server
app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")