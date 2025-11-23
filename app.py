import numpy as np
from flask import Flask, request, render_template
import pickle
from huggingface_hub import hf_hub_download

app = Flask(__name__)

# cargar modelo remoto
model_path = hf_hub_download(
    repo_id="sophie-muriel/insurance-renewal",
    filename="insurance_renewal_model.pkl")

# cargar scaler remoto
scaler_path = hf_hub_download(
    repo_id="sophie-muriel/insurance-renewal",
    filename="scaler.pkl"
)

with open(model_path, "rb") as f:
    model = pickle.load(f)  # abrir modelo

with open(scaler_path, "rb") as f:
    scaler = pickle.load(f)  # abrir scaler


# cargar modelo local
# model = pickle.load(open("insurance_renewal_model.pkl", "rb"))

# cargar scaler local
# scaler = pickle.load(open("scaler.pkl", "rb"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    # features del modelo en orden
    form_fields = [
        "perc_premium_paid_by_cash_credit",
        "income",
        "application_underwriting_score",
        "age_in_years",
        "total_late_payments",
        "has_late_payments"
    ]

    form_values = [float(request.form[field]) for field in form_fields]

    # transformación logarítmica a 'income'
    form_values[1] = np.log(form_values[1] + 1)

    full_numeric = np.array([[
        form_values[0],  # perc_premium
        form_values[1],  # income (logged)
        form_values[2],  # app_score
        0,               # no_of_premiums_paid (dummy)
        0,               # premium (dummy)
        form_values[3],  # age
        form_values[4]   # total_late
    ]])

    scaled_full = scaler.transform(full_numeric)

    # features finales para el modelo
    selected_indices = [0, 1, 2, 5, 6]
    X_final = scaled_full[:, selected_indices]

    # feature binaria (no escalada)
    has_late = form_values[5]
    X_input = np.hstack([X_final, np.array([[has_late]])])

    # predicción
    prediction = model.predict(X_input)[0]
    prob_renew = model.predict_proba(X_input)[0][1]

    # generar texto del resultado
    if prediction == 1:
        result_text = (
            f"RENOVACIÓN PROBABLE // PROBABILIDAD: "
            f"<span class='prob-accent'>{prob_renew*100:.1f}%</span>"
        )
    else:
        result_text = (
            f"RENOVACIÓN IMPROBABLE (CHURN) // PROBABILIDAD: "
            f"<span class='prob-accent'>{prob_renew*100:.1f}%</span>"
        )

    return render_template("index.html", prediction_text=result_text)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
