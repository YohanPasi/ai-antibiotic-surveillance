import React, { useState, useEffect } from 'react';
import Sparkline from './Sparkline';

const AntibiogramTable = ({ wardId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState('current'); // 'current' or 'predicted'

    useEffect(() => {
        setLoading(true);
        const url = wardId
            ? `http://localhost:8000/api/analysis/antibiogram?ward=${wardId}`
            : `http://localhost:8000/api/analysis/antibiogram`;

        fetch(url)
            .then(res => res.json())
            .then(resData => {
                setData(resData);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, [wardId]);

    const getColorClass = (value) => {
        if (value >= 80) return 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200 border-emerald-200 dark:border-emerald-800';
        if (value >= 60) return 'bg-amber-100 dark:bg-yellow-900/40 text-amber-800 dark:text-yellow-200 border-amber-200 dark:border-yellow-800';
        return 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 border-red-200 dark:border-red-800';
    };

    if (loading) return <div className="text-slate-500 dark:text-gray-400 p-4">Loading Antibiogram...</div>;
    if (!data || !data.matrix) return <div className="text-slate-500 dark:text-gray-400 p-4">No Data Available</div>;

    const { matrix, antibiotics, scope } = data;
    const organisms = Object.keys(matrix).sort();

    return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-8 shadow-sm transition-colors duration-300">
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        🧬 {scope} Antibiogram
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">
                        Cumulative Sensitivity Pattern Matrix (% Susceptible)
                    </p>
                </div>

                {/* Toggle Switch */}
                <div className="bg-slate-100 dark:bg-gray-900 p-1 rounded-lg border border-gray-200 dark:border-gray-700 flex">
                    <button
                        onClick={() => setViewMode('current')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'current'
                            ? 'bg-white dark:bg-blue-600 text-blue-700 dark:text-white shadow-sm'
                            : 'text-slate-500 dark:text-gray-400 hover:text-slate-800 dark:hover:text-white'
                            }`}
                    >
                        Current Observed
                    </button>
                    <button
                        onClick={() => setViewMode('predicted')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'predicted'
                            ? 'bg-white dark:bg-purple-600 text-purple-700 dark:text-white shadow-sm'
                            : 'text-slate-500 dark:text-gray-400 hover:text-slate-800 dark:hover:text-white'
                            }`}
                    >
                        🔮 AI Predicted (Next Week)
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-center border-collapse">
                    <thead>
                        <tr>
                            <th className="p-3 text-left text-slate-500 dark:text-gray-400 font-semibold border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 sticky left-0 z-10 w-[200px]">
                                Organism
                            </th>
                            {antibiotics.map(abx => (
                                <th key={abx} className="p-3 text-slate-700 dark:text-gray-300 font-semibold border-b border-gray-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-900/30 min-w-[100px]">
                                    {abx}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {organisms.map(org => (
                            <tr key={org} className="hover:bg-slate-50 dark:hover:bg-gray-700/30 transition-colors">
                                <td className="p-4 text-left font-bold text-slate-800 dark:text-white border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 sticky left-0 border-r border-gray-200 dark:border-gray-800">
                                    {org}
                                </td>
                                {antibiotics.map(abx => {
                                    const cellData = matrix[org][abx];
                                    if (!cellData) {
                                        return <td key={abx} className="p-3 border-b border-gray-200 dark:border-gray-700 text-slate-400 dark:text-gray-600">-</td>;
                                    }

                                    const val = viewMode === 'current' ? cellData.current : cellData.predicted;
                                    const history = cellData.history || [];

                                    return (
                                        <td key={abx} className="p-1 border-b border-gray-200 dark:border-gray-700">
                                            <div className={`py-1 px-1 rounded border ${getColorClass(val)} font-mono flex flex-col items-center justify-center h-16 transition-colors duration-300`}>
                                                <span className="text-sm font-bold">{val.toFixed(0)}%</span>
                                                {viewMode === 'current' && history.length > 1 && (
                                                    <div className="mt-1 opacity-80 hover:opacity-100">
                                                        <Sparkline data={history} color={val >= 60 ? "#065f46" : "#7f1d1d"} />
                                                    </div>
                                                )}
                                                {viewMode === 'predicted' && (
                                                    <span className="text-[10px] mt-1 text-purple-600 dark:text-purple-200 opacity-70">
                                                        Pred
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 flex gap-4 text-xs text-slate-500 dark:text-gray-400 justify-end">
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-emerald-100 dark:bg-green-900/40 border border-emerald-300 dark:border-green-800 rounded"></span> Substantial (&gt;80%)
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-amber-100 dark:bg-yellow-900/40 border border-amber-300 dark:border-yellow-800 rounded"></span> Moderate (60-80%)
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-100 dark:bg-red-900/40 border border-red-300 dark:border-red-800 rounded"></span> Resistant (&lt;60%)
                </div>
            </div>
        </div>
    );
};

export default AntibiogramTable;
