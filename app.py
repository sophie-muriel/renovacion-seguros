import numpy as np
from flask import Flask, request, render_template
import pickle

app = Flask(__name__)

model = pickle.load(open("insurance_renewal_model.pkl", "rb"))  # cargar modelo
scaler = pickle.load(open("scaler.pkl", "rb"))                  # cargar scaler


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
        result_text = f"RENOVACIÓN PROBABLE // CONFIANZA: {prob_renew*100:.1f}%"
    else:
        result_text = f"RENOVACIÓN IMPROBABLE (CHURN) // CONFIANZA: {prob_renew*100:.1f}%"

    return render_template("index.html", prediction_text=result_text)


if __name__ == "__main__":
    app.run()
