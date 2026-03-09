import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, RefreshCw, Info, FlaskConical } from 'lucide-react';

const API = 'http://localhost:8000';

// Human-friendly label for data quality
const getQualityLabel = (ratio) => {
    if (ratio >= 0.9) return { label: 'Complete', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' };
    if (ratio >= 0.7) return { label: 'Sufficient', color: 'text-amber-700 bg-amber-50 border-amber-200' };
    return { label: 'Partial', color: 'text-red-700 bg-red-50 border-red-200' };
};

const STPValidation = () => {
    const [validations, setValidations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [minCompleteness, setMinCompleteness] = useState(0.7);

    useEffect(() => { fetchValidations(); }, [minCompleteness]);

    const fetchValidations = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/stp/feedback/validation?min_completeness=${minCompleteness}`);
            if (res.ok) {
                const data = await res.json();
                setValidations(data.validations || []);
            }
        } catch { /* silent */ }
        finally { setLoading(false); }
    };

    const passCount = validations.filter(v => v.status === 'PASS').length;
    const missCount = validations.filter(v => v.status === 'MISS').length;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Prediction vs. Reality</h1>
                    <p className="text-sm text-slate-500 mt-0.5">Comparing what the system predicted to what was actually observed in the lab</p>
                </div>
                <button
                    onClick={fetchValidations}
                    className="self-start sm:self-auto flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors shadow-sm"
                >
                    <RefreshCw className="w-4 h-4" /> Refresh
                </button>
            </div>

            {/* Summary Boxes */}
            {validations.length > 0 && (
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4 text-center shadow-sm">
                        <div className="text-3xl font-black text-slate-800 dark:text-white">{validations.length}</div>
                        <div className="text-xs text-slate-500 mt-1">Records Compared</div>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-emerald-100 p-4 text-center shadow-sm">
                        <div className="text-3xl font-black text-emerald-600">{passCount}</div>
                        <div className="text-xs text-slate-500 mt-1">Accurate Predictions</div>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-red-100 p-4 text-center shadow-sm">
                        <div className="text-3xl font-black text-red-600">{missCount}</div>
                        <div className="text-xs text-slate-500 mt-1">Needs Attention</div>
                    </div>
                </div>
            )}

            {/* Filter */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm p-4 flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-3">
                    <FlaskConical className="w-4 h-4 text-slate-400" />
                    <label className="text-sm font-semibold text-slate-600 dark:text-gray-300">Minimum lab data completeness:</label>
                    <select
                        value={minCompleteness}
                        onChange={e => setMinCompleteness(parseFloat(e.target.value))}
                        className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
                    >
                        <option value="0.5">At least 50%</option>
                        <option value="0.7">At least 70% (Recommended)</option>
                        <option value="0.8">At least 80%</option>
                        <option value="0.9">At least 90%</option>
                    </select>
                </div>
                <div className="flex items-start gap-2 text-xs text-slate-400 ml-auto">
                    <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                    Higher completeness = more reliable comparison
                </div>
            </div>

            {/* Results */}
            {loading ? (
                <div className="flex items-center justify-center h-40">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                </div>
            ) : validations.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 py-16 text-center">
                    <FlaskConical className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                    <p className="font-semibold text-slate-500">No comparison data yet</p>
                    <p className="text-sm text-slate-400 mt-1">Submit antibiogram results first to generate comparisons</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {validations.map((v, idx) => {
                        const isPass = v.status === 'PASS';
                        const quality = getQualityLabel(v.completeness_ratio);
                        const errorPct = (v.absolute_error * 100).toFixed(1);
                        return (
                            <div
                                key={idx}
                                className={`bg-white dark:bg-gray-800 rounded-xl border shadow-sm p-5 transition-shadow hover:shadow-md ${isPass ? 'border-emerald-100' : 'border-red-100'}`}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex items-start gap-3 min-w-0">
                                        {isPass
                                            ? <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                                            : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                                        }
                                        <div className="min-w-0">
                                            <h3 className="font-semibold text-slate-800 dark:text-white">{v.ward} — {v.organism}</h3>
                                            <p className="text-sm text-slate-500">{v.antibiotic}</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-col items-end gap-2 flex-shrink-0">
                                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${isPass ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                                            {isPass ? '✓ Accurate' : '⚠ Discrepancy'}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${quality.color}`}>
                                            Data: {quality.label}
                                        </span>
                                    </div>
                                </div>

                                {/* Rates Comparison */}
                                <div className="mt-4 grid grid-cols-3 gap-3">
                                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
                                        <p className="text-xs text-slate-500 mb-1">Predicted</p>
                                        <p className="text-xl font-bold text-slate-700 dark:text-gray-200">{(v.predicted_rate * 100).toFixed(1)}%</p>
                                    </div>
                                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
                                        <p className="text-xs text-slate-500 mb-1">Observed (Lab)</p>
                                        <p className="text-xl font-bold text-slate-700 dark:text-gray-200">{(v.observed_rate * 100).toFixed(1)}%</p>
                                    </div>
                                    <div className={`rounded-lg p-3 text-center ${parseFloat(errorPct) > 10 ? 'bg-red-50 dark:bg-red-900/20' : 'bg-emerald-50 dark:bg-emerald-900/20'}`}>
                                        <p className="text-xs text-slate-500 mb-1">Difference</p>
                                        <p className={`text-xl font-bold ${parseFloat(errorPct) > 10 ? 'text-red-600' : 'text-emerald-600'}`}>{errorPct}%</p>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default STPValidation;
