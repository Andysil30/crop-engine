import pandas as pd, joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier

def add_features(df):
    df = df.copy()
    df["N_P_ratio"] = df["N"] / (df["P"] + 1)
    df["N_K_ratio"] = df["N"] / (df["K"] + 1)
    df["P_K_ratio"] = df["P"] / (df["K"] + 1)
    df["NPK_total"] = df["N"] + df["P"] + df["K"]
    df["water_stress"] = df["rainfall"] / (df["temperature"] + 1)
    df["ph_acidic"] = (df["ph"] < 5.5).astype(int)
    df["ph_alkaline"] = (df["ph"] > 7.5).astype(int)
    return df

if __name__ == "__main__":
    df = pd.read_csv("data/Crop_recommendation.csv")
    le = LabelEncoder()
    y = le.fit_transform(df["label"])
    X = add_features(df.drop(columns="label"))

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    models = {
        "RandomForest": RandomForestClassifier(n_estimators=300, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=300, learning_rate=0.1, eval_metric="mlogloss"),
    }
    best_name, best_model, best_score = None, None, 0
    for name, m in models.items():
        cv = cross_val_score(m, X_tr, y_tr, cv=5).mean()
        m.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, m.predict(X_te))
        print(f"{name}: CV={cv:.4f} Test={acc:.4f}")
        if acc > best_score:
            best_name, best_model, best_score = name, m, acc

    print(classification_report(y_te, best_model.predict(X_te), target_names=le.classes_))
    joblib.dump(best_model, "models/model.pkl")
    joblib.dump(le, "models/label_encoder.pkl")
    joblib.dump(list(X.columns), "models/features.pkl")
    print("Saved:", best_name)