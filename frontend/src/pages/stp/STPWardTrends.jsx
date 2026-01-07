
import React from 'react';
import TrendChart from '../../components/stp/TrendChart';

const STPWardTrends = () => {
    // Mock Data
    const trendData = [
        { date: '2025-01-01', resistance_rate: 0.12 },
        { date: '2025-01-08', resistance_rate: 0.14 },
        { date: '2025-01-15', resistance_rate: 0.13 },
        { date: '2025-01-22', resistance_rate: 0.16 },
        { date: '2025-01-29', resistance_rate: 0.15 },
    ];

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Ward Resistance Trends</h2>
            <p className="text-slate-500 mb-4">Descriptive Surveillance (No AI Predictions)</p>

            <div className="grid grid-cols-1 gap-6">
                <TrendChart data={trendData} title="ICU: E. coli Resistance Rate (Weekly)" />

                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <h4 className="text-sm font-bold text-slate-700 dark:text-gray-200 mb-4">Ward Profile Heatmap</h4>
                    <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg text-slate-400">
                        Heatmap Component Placeholder
                    </div>
                </div>
            </div>
        </div>
    );
};

export default STPWardTrends;
