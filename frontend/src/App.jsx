import { useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

const TRANSACTION_TYPES = [
  { value: "ATM", label: "ATM" },
  { value: "POS", label: "POS" },
  { value: "ONLINE", label: "Online" },
];

const LOCATIONS = [
  { value: "ABUJA", label: "Abuja" },
  { value: "LAGOS", label: "Lagos" },
  { value: "KANO", label: "Kano" },
  { value: "OTHERS", label: "Others" },
];

function App() {
  const [form, setForm] = useState({
    amount: "",
    time: "",
    transaction_type: "ATM",
    location: "LAGOS",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  const updateField = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const checkHealth = async () => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        amount: Number(form.amount),
        time: Number(form.time),
        transaction_type: form.transaction_type,
        location: form.location,
      };

      const res = await fetch(`${API_BASE}/api/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Prediction failed");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Fraud Detection</h1>
        <p className="subtitle">Check if a transaction is likely fraudulent</p>
      </header>

      <section className="card">
        <div className="health-row">
          <button type="button" className="secondary" onClick={checkHealth}>
            Check API Health
          </button>
          {health && (
            <span className="health-status">
              Status: {health.status} · Model loaded: {String(health.model_loaded)}
            </span>
          )}
        </div>
      </section>

      <section className="card">
        <form onSubmit={handleSubmit} className="form">
          <div className="field">
            <label htmlFor="amount">Amount</label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min="0"
              required
              value={form.amount}
              onChange={updateField("amount")}
              placeholder="e.g. 15000.50"
            />
          </div>

          <div className="field">
            <label htmlFor="time">Time of day (seconds since midnight)</label>
            <input
              id="time"
              type="number"
              min="0"
              max="86399"
              required
              value={form.time}
              onChange={updateField("time")}
              placeholder="e.g. 43200 (12:00 PM)"
            />
            <small className="help">Value between 0 - 86399</small>
          </div>

          <div className="field">
            <label htmlFor="transaction_type">Transaction Type</label>
            <select
              id="transaction_type"
              value={form.transaction_type}
              onChange={updateField("transaction_type")}
            >
              {TRANSACTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="location">Location</label>
            <select
              id="location"
              value={form.location}
              onChange={updateField("location")}
            >
              {LOCATIONS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" className="primary" disabled={loading}>
            {loading ? "Predicting..." : "Predict Fraud"}
          </button>
        </form>
      </section>

      {(result || error) && (
        <section className="card">
          {error && (
            <div className="alert error">
              <strong>Error:</strong> {error}
            </div>
          )}
          {result && (
            <div className={`alert ${result.prediction === "fraudulent" ? "danger" : "success"}`}>
              <div className="result-row">
                <span className="result-label">Prediction</span>
                <span className="result-value">{result.prediction.toUpperCase()}</span>
              </div>
              {result.fraud_probability !== null && (
                <div className="result-row">
                  <span className="result-label">Fraud Probability</span>
                  <span className="result-value">{(result.fraud_probability * 100).toFixed(2)}%</span>
                </div>
              )}
              <div className="result-row">
                <span className="result-label">Model Version</span>
                <span className="result-value">{result.model_version}</span>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default App;
