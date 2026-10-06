import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from ml.train import add_features

df = pd.read_csv("data/Crop_recommendation.csv")
y = LabelEncoder().fit_transform(df["label"])
raw = df.drop(columns="label")
engineered = add_features(raw)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for name, X in [("Raw features only (7)", raw), ("With engineered features (14)", engineered)]:
    scores = cross_val_score(RandomForestClassifier(n_estimators=300, random_state=42), X, y, cv=cv)
    print(f"{name}: mean={scores.mean():.4f}  std={scores.std():.4f}")