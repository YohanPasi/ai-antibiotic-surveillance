
import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';

const STPValidation = () => {
    const [validations, setValidations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [minCompleteness, setMinCompleteness] = useState(0.7);

    useEffect(() => {
        fetchValidations();
    }, [minCompleteness]);

    const fetchValidations = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/stp/feedback/validation?min_completeness=${minCompleteness}`);
            if (response.ok) {
                const data = await response.json();
                setValidations(data.validations || []);
            }
        } catch (error) {
            console.error('Failed to fetch validations:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'PASS':
                return <CheckCircle className="text-green-600" size={20} />;
            case 'MISS':
                return <XCircle className="text-red-600" size={20} />;
            default:
                return <AlertTriangle className="text-amber-600" size={20} />;
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'PASS':
                return 'bg-green-50 border-green-200';
            case 'MISS':
                return 'bg-red-50 border-red-200';
            default:
                return 'bg-amber-50 border-amber-200';
        }
    };

    const getCompletenessColor = (ratio) => {
        if (ratio >= 0.9) return 'text-green-700';
        if (ratio >= 0.7) return 'text-amber-700';
        return 'text-red-700';
    };

    return (
        <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                    🔍 <strong>Prediction Validation:</strong> Compare model predictions against observed outcomes.
                    Green = within confidence interval, Red = CI violation. Only antibiograms meeting quality thresholds are shown.
                </p>
            </div>

            <div className="flex justify-between items-center">
                <div>
                    <label className="text-sm font-medium mr-3">Minimum Completeness:</label>
                    <select
                        value={minCompleteness}
                        onChange={(e) => setMinCompleteness(parseFloat(e.target.value))}
                        className="border rounded px-3 py-2 text-sm"
                    >
                        <option value="0.5">50%</option>
                        <option value="0.7">70% (Recommended)</option>
                        <option value="0.8">80%</option>
                        <option value="0.9">90%</option>
                    </select>
                </div>
                <button
                    onClick={fetchValidations}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                >
                    <RefreshCw size={16} /> Refresh
                </button>
            </div>

            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading validations...</div>
            ) : (
                <div className="space-y-4">
                    {validations.map((v, idx) => (
                        <div key={idx} className={`border rounded-lg p-4 ${getStatusColor(v.status)}`}>
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        {getStatusIcon(v.status)}
                                        <h3 className="font-semibold">
                                            {v.ward} — {v.organism} / {v.antibiotic}
                                        </h3>
                                    </div>

                                    <div className="grid grid-cols-5 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-600">Predicted:</span>
                                            <span className="ml-2 font-medium">{(v.predicted_rate * 100).toFixed(1)}%</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-600">Observed:</span>
                                            <span className="ml-2 font-medium">{(v.observed_rate * 100).toFixed(1)}%</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-600">Error:</span>
                                            <span className="ml-2 font-medium">{(v.absolute_error * 100).toFixed(1)}%</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-600">CI Status:</span>
                                            <span className={`ml-2 font-medium ${v.within_ci ? 'text-green-700' : 'text-red-700'}`}>
                                                {v.within_ci ? 'Within CI' : 'CI Violation'}
                                            </span>
                                        </div>
                                        {/* FIX #3: Completeness Display */}
                                        <div>
                                            <span className="text-gray-600">Completeness:</span>
                                            <span className={`ml-2 font-medium ${getCompletenessColor(v.completeness_ratio)}`}>
                                                {(v.completeness_ratio * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}

                    {validations.length === 0 && (
                        <div className="text-center py-12 text-gray-500">
                            No validation data available. Submit antibiograms to generate comparisons.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default STPValidation;
