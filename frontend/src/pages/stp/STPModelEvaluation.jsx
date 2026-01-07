
import React from 'react';
import TrendChart from '../../components/stp/TrendChart';

const STPModelEvaluation = () => {
    // Mock Data
    const calibrationData = [
        { date: '0.1', resistance_rate: 0.12 },
        { date: '0.3', resistance_rate: 0.28 },
        { date: '0.5', resistance_rate: 0.49 },
        { date: '0.7', resistance_rate: 0.72 },
        { date: '0.9', resistance_rate: 0.88 },
    ];

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Model Evaluation</h2>
            <p className="text-slate-500">Governance & Clinical Validation Metrics (M41-M55)</p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <h3 className="font-bold text-lg mb-4">Metric Priority</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg border border-green-100">
                            <span className="font-bold text-green-800">NPV (Negative Predictive Value)</span>
                            <span className="text-2xl font-bold text-green-700">0.98</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="font-medium text-gray-600">Sensitivity</span>
                            <span className="text-xl font-bold text-gray-700">0.85</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span className="font-medium text-gray-600">AUROC</span>
                            <span className="text-xl font-bold text-gray-700">0.91</span>
                        </div>
                    </div>
                </div>

                <TrendChart data={calibrationData} title="Reliability Curve (Calibration)" />
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                <h3 className="font-bold text-lg mb-4">Stability Analysis (Jaccard Index)</h3>
                <div className="h-40 flex items-center justify-center bg-gray-50 rounded text-slate-400">
                    Stability Chart Placeholder
                </div>
            </div>
        </div>
    );
};

export default STPModelEvaluation;
