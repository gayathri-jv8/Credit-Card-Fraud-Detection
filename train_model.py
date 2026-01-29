import pandas as pd
from sklearn.ensemble import IsolationForest
import pickle

# Sample transaction data (NORMAL behavior)
data = {
    "amount": [500, 1000, 2000, 3000, 1500, 2500, 4000, 5000, 1200, 1800]
}

df = pd.DataFrame(data)

# Train Isolation Forest (anomaly detection)
model = IsolationForest(
    n_estimators=100,
    contamination=0.1,
    random_state=42
)

model.fit(df)

# Save model
with open("fraud_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Fraud Detection Model Trained & Saved!")

