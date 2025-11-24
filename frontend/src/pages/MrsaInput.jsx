import React, { useState } from "react";

function MrsaInput() {
  const [form, setForm] = useState({
    sample_id: "",
    ward: "",
    sample_type: "",
    organism: "",
    gram: "",
    collection_time: "",
  });

  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const submitPredict = async () => {
    const res = await fetch("http://127.0.0.1:8000/mrsa/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const json = await res.json();
    setResult(json);
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">MRSA Prediction Input</h1>

      <div className="space-y-3">
        {Object.keys(form).map((key) => (
          <input
            key={key}
            name={key}
            value={form[key]}
            onChange={handleChange}
            placeholder={key}
            className="w-full border p-2 rounded"
          />
        ))}

        <button
          onClick={submitPredict}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Predict
        </button>
      </div>

      {result && (
        <div className="mt-6 bg-white shadow p-4 rounded">
          <h2 className="font-semibold">Prediction Result</h2>
          <pre className="text-sm mt-2">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default MrsaInput;
