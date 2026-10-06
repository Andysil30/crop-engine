from pathlib import Path
import pandas as pd

# Find the CSV no matter where we run from
DATA = Path(__file__).resolve().parent.parent / "data" / "Crop_recommendation.csv"

# The "recipe" for each crop: average N, P, K and pH
PROFILES = pd.read_csv(DATA).groupby("label")[["N", "P", "K", "ph"]].mean()

TOLERANCE = 10        # gaps smaller than this are "close enough"
PH_TOLERANCE = 0.5

# Which product gives which nutrient, and what fraction of the bag is the nutrient
PRODUCTS = {
    "N": [("Urea", 0.46), ("CAN", 0.26)],
    "P": [("DAP", 0.46)],
    "K": [("MOP", 0.60)],
}

def fertilizer_plan(crop, N, P, K, ph):
    ideal = PROFILES.loc[crop]
    actual = {"N": N, "P": P, "K": K}
    nutrients = []

    for nut in ["N", "P", "K"]:
        gap = float(ideal[nut] - actual[nut])    # positive = soil is short
        if gap > TOLERANCE:
            status = "low"
            products = [
                {"name": name, "amount": round(gap / frac, 1)}
                for name, frac in PRODUCTS[nut]
            ]
        elif gap < -TOLERANCE:
            status, products = "high", []        # too much already, add none
        else:
            status, products = "ok", []
        nutrients.append({
            "nutrient": nut,
            "status": status,
            "your_value": round(float(actual[nut]), 1),
            "ideal_value": round(float(ideal[nut]), 1),
            "gap": round(gap, 1),
            "products": products,
        })

    ph_gap = float(ideal["ph"] - ph)
    if ph_gap > PH_TOLERANCE:
        ph_advice = "add_lime"            # soil too acidic
    elif ph_gap < -PH_TOLERANCE:
        ph_advice = "add_sulfur"          # soil too alkaline
    else:
        ph_advice = "ph_ok"

    return {
        "crop": crop,
        "nutrients": nutrients,
        "ph": {"your_value": ph, "ideal_value": round(float(ideal["ph"]), 1), "advice": ph_advice},
    }