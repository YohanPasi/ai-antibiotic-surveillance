import React, { useState } from 'react';
import PredictionPanel from './PredictionPanel';

// Simple Input Field Component
const InputField = ({ label, name, type = "text", value, onChange, options = null }) => (
    <div className="space-y-1">
        <label className="text-sm font-medium text-gray-400">{label}</label>
        {options ? (
            <select
                name={name}
                value={value}
                onChange={onChange}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors"
            >
                {options.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                ))}
            </select>
        ) : (
            <input
                type={type}
                name={name}
                value={value}
                onChange={onChange}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors"
            />
        )}
    </div>
);

export default function MRSAPage() {
    const [formData, setFormData] = useState({
        age: 65,
        gender: 'Male',
        ward: 'ICU',
        sample_type: 'Blood',
        cell_count: 'Unknown',
        growth_time: 24,
        pus_type: 'Unknown',
        gram_positivity: 'Unknown'
    });

    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handlePredict = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setPrediction(null);

        try {
            const token = localStorage.getItem("token");
            const response = await fetch('/api/mrsa/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Prediction failed');
            }

            // Map backend response to PredictionPanel expected format
            setPrediction({
                prediction: data.mrsa_probability * 100, // Convert to %
                lower_bound: Math.max(0, (data.mrsa_probability * 100) - 5), // Mock CI
                upper_bound: Math.min(100, (data.mrsa_probability * 100) + 5), // Mock CI
                alert_level: data.risk_band.toLowerCase(),
                model_used: data.model_version || "Random Forest (C)",
                confidence: 'High',
                assessment_id: data.assessment_id
            });

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <header className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">MRSA Risk Assessment</h1>
                    <p className="text-gray-400 mt-1">AI-Driven Pre-AST Prediction Tool (Stage F Complete)</p>
                </div>
                <div className="text-xs text-gray-500 px-3 py-1 bg-dark-bg rounded border border-dark-border">
                    v2.1 (Explainable AI)
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Input Form */}
                <div className="card lg:col-span-1 border-t-4 border-t-primary-500">
                    <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <span>📝</span> Clinical Features
                    </h2>

                    <form onSubmit={handlePredict} className="space-y-5">
                        <div className="grid grid-cols-2 gap-4">
                            <InputField
                                label="Age" name="age" type="number"
                                value={formData.age} onChange={handleChange}
                            />
                            <InputField
                                label="Gender" name="gender"
                                value={formData.gender} onChange={handleChange}
                                options={['Male', 'Female']}
                            />
                        </div>

                        <InputField
                            label="Ward Location" name="ward"
                            value={formData.ward} onChange={handleChange}
                            options={['ICU', 'Ward 01', 'Ward 02', 'A&E']}
                        />

                        <InputField
                            label="Specimen Type" name="sample_type"
                            value={formData.sample_type} onChange={handleChange}
                            options={['Blood', 'Urine', 'Pus', 'Sputum', 'Wound Swab']}
                        />

                        <div className="grid grid-cols-2 gap-4">
                            <InputField
                                label="Growth Time (h)" name="growth_time" type="number"
                                value={formData.growth_time} onChange={handleChange}
                            />
                            <InputField
                                label="Cell Count" name="cell_count"
                                value={formData.cell_count} onChange={handleChange}
                                options={['Unknown', 'Low', 'Moderate', 'Many', 'Plenty']}
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-900/20 border border-red-500/50 rounded text-red-300 text-sm">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-bold rounded-lg shadow-lg shadow-primary-900/30 transition-all transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Running AI Model...' : 'Run Prediction'}
                        </button>
                    </form>
                </div>

                {/* Right Column: Prediction Panel */}
                <div className="lg:col-span-2">
                    <PredictionPanel
                        prediction={prediction}
                        loading={loading}
                        organism="Staphylococcus aureus"
                        antibiotic="Cefoxitin (MRSA)"
                    />
                </div>
            </div>
        </div>
    );
}
