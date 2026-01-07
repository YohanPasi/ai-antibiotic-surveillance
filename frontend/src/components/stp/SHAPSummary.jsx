
import React from 'react';

const SHAPSummary = ({ features }) => {
    // Expects features = [{ name: 'Previous Resistance', value: 0.15, type: 'positive' }]

    // Sort by absolute impact
    const sortedDetails = [...features].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 5);
    const maxValue = Math.max(...sortedDetails.map(f => Math.abs(f.value)));

    return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
            <h4 className="text-sm font-bold text-slate-700 dark:text-gray-200 mb-3">Top Risk Drivers (SHAP)</h4>
            <div className="space-y-3">
                {sortedDetails.map((feat, idx) => (
                    <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs">
                            <span className="text-slate-600 dark:text-gray-400 font-medium truncate w-2/3">{feat.name}</span>
                            <span className="text-slate-500 dark:text-gray-500 font-mono">{(feat.value).toFixed(3)}</span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5 flex items-center relative">
                            {/* Center line */}
                            <div className="absolute left-1/2 w-px h-full bg-gray-300 dark:bg-gray-600"></div>

                            {/* Bar logic: if positive, start at 50% go right. if negative, start at 50% - width go left. */}
                            {/* Simplification for demo: just show magnitude and color */}
                            <div
                                className={`h-full rounded-full ${feat.value > 0 ? 'bg-red-400' : 'bg-blue-400'}`}
                                style={{
                                    width: `${(Math.abs(feat.value) / maxValue) * 50}%`,
                                    marginLeft: feat.value > 0 ? '50%' : `${50 - ((Math.abs(feat.value) / maxValue) * 50)}%`
                                }}
                            />
                        </div>
                    </div>
                ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-3 text-center">Red = Increases Risk | Blue = Decreases Risk</p>
        </div>
    );
};

export default SHAPSummary;
