import React from 'react';
import { Info } from 'lucide-react';

// Human-readable factor name mapping
const FACTOR_LABELS = {
    'Signal Strength': 'Resistance trend strength',
    'Detection Method': 'Detection method used',
    'prior_resistance': 'Prior resistance history',
    'ward_prevalence': 'Ward-level prevalence',
    'rolling_slope': 'Trend direction',
    'volatility': 'Rate of change',
};

const getLabel = (name) => FACTOR_LABELS[name] || name;

/**
 * SHAPSummary — shows key factors influencing the prediction in plain English.
 * Features: [{ name, value }]
 */
const SHAPSummary = ({ features = [] }) => {
    if (!features || features.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-xl border border-gray-100 dark:border-gray-600 p-4 text-center text-xs text-slate-400">
                No factor data available
            </div>
        );
    }

    const sorted = [...features].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 4);
    const maxVal = Math.max(...sorted.map(f => Math.abs(f.value)), 0.001);

    return (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl border border-gray-100 dark:border-gray-600 p-4">
            <div className="flex items-center gap-1.5 mb-3">
                <Info className="w-3.5 h-3.5 text-slate-400" />
                <h4 className="text-xs font-bold text-slate-600 dark:text-gray-300 uppercase tracking-wide">Key Contributing Factors</h4>
            </div>
            <div className="space-y-3">
                {sorted.map((feat, idx) => {
                    const pct = (Math.abs(feat.value) / maxVal) * 100;
                    const isIncreasing = feat.value > 0;
                    return (
                        <div key={idx}>
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-slate-600 dark:text-gray-400 truncate mr-2">{getLabel(feat.name)}</span>
                                <span className={`text-[10px] font-semibold flex-shrink-0 ${isIncreasing ? 'text-red-600' : 'text-blue-600'}`}>
                                    {isIncreasing ? '▲ Raises Risk' : '▼ Lowers Risk'}
                                </span>
                            </div>
                            <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all duration-700 ${isIncreasing ? 'bg-red-400' : 'bg-blue-400'}`}
                                    style={{ width: `${pct}%` }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default SHAPSummary;
