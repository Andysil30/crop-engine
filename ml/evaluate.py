import pandas as pd, joblib, matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.preprocessing import LabelEncoder
from ml.train import add_features

df = pd.read_csv("data/Crop_recommendation.csv")
le = LabelEncoder()
y = le.fit_transform(df["label"])
X = add_features(df.drop(columns="label"))
features = joblib.load("models/features.pkl")
model = joblib.load("models/model.pkl")

_, X_te, _, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
X_te = X_te[features]

# 1. Confusion matrix
fig, ax = plt.subplots(figsize=(12, 12))
ConfusionMatrixDisplay.from_estimator(
    model, X_te, y_te, display_labels=le.classes_,
    xticks_rotation=90, ax=ax, colorbar=False)
plt.tight_layout()
plt.savefig("models/confusion_matrix.png", dpi=150)

# 2. Feature importance
imp = pd.Series(model.feature_importances_, index=features).sort_values()
plt.figure(figsize=(8, 6))
imp.plot(kind="barh", color="#2e7d32")
plt.title("Feature importance")
plt.tight_layout()
plt.savefig("models/feature_importance.png", dpi=150)

print("Saved two images in the models folder")