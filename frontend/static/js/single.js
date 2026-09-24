const form = document.getElementById("check-form");
const submitBtn = document.getElementById("submit-btn");
const loadingNote = document.getElementById("loading-note");
const errorBox = document.getElementById("error-box");
const result = document.getElementById("result");
const probValue = document.getElementById("prob-value");
const riskPill = document.getElementById("risk-pill");
const meterFill = document.getElementById("meter-fill");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.classList.remove("is-visible");
  result.classList.remove("is-visible");
  submitBtn.disabled = true;
  loadingNote.style.display = "inline";

  const payload = {
    amount: parseFloat(document.getElementById("amount").value),
    transaction_type: document.getElementById("transaction_type").value,
    hour: parseInt(document.getElementById("hour").value, 10),
    account_age_days: parseInt(document.getElementById("account_age_days").value, 10),
    distance_from_home_km: parseFloat(document.getElementById("distance_from_home_km").value),
    distance_from_last_txn_km: parseFloat(document.getElementById("distance_from_last_txn_km").value),
    num_txns_last_24h: parseInt(document.getElementById("num_txns_last_24h").value, 10),
    is_foreign: document.getElementById("is_foreign").checked ? 1 : 0,
    is_high_risk_merchant: document.getElementById("is_high_risk_merchant").checked ? 1 : 0,
  };

  try {
    const res = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Prediction failed.");

    const pct = Math.round(data.fraud_probability * 1000) / 10;
    probValue.textContent = `${pct}%`;
    meterFill.style.width = `${pct}%`;
    riskPill.textContent = `${data.risk_level} risk`;
    riskPill.className = `risk-pill ${data.risk_level}`;
    meterFill.className = `meter-fill ${data.risk_level}`;
    result.classList.add("is-visible");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("is-visible");
  } finally {
    submitBtn.disabled = false;
    loadingNote.style.display = "none";
  }
});
