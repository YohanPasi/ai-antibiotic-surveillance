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
        if (value >= 80) return 'bg-green-900/40 text-green-200 border-green-800';
        if (value >= 60) return 'bg-yellow-900/40 text-yellow-200 border-yellow-800';
        return 'bg-red-900/40 text-red-200 border-red-800';
    };

    if (loading) return <div className="text-gray-400 p-4">Loading Antibiogram...</div>;
    if (!data || !data.matrix) return <div className="text-gray-400 p-4">No Data Available</div>;

    const { matrix, antibiotics, scope } = data;
    const organisms = Object.keys(matrix).sort();

    return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8 shadow-xl">
            <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        🧬 {scope} Antibiogram
                    </h2>
                    <p className="text-sm text-gray-400 mt-1">
                        Cumulative Sensitivity Pattern Matrix (% Susceptible)
                    </p>
                </div>

                {/* Toggle Switch */}
                <div className="bg-gray-900 p-1 rounded-lg border border-gray-700 flex">
                    <button
                        onClick={() => setViewMode('current')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'current'
                            ? 'bg-blue-600 text-white shadow'
                            : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        Current Observed
                    </button>
                    <button
                        onClick={() => setViewMode('predicted')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'predicted'
                            ? 'bg-purple-600 text-white shadow'
                            : 'text-gray-400 hover:text-white'
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
                            <th className="p-3 text-left text-gray-400 font-medium border-b border-gray-700 bg-gray-900/50 sticky left-0 z-10">
                                Organism
                            </th>
                            {antibiotics.map(abx => (
                                <th key={abx} className="p-3 text-gray-300 font-medium border-b border-gray-700 bg-gray-900/30 min-w-[100px]">
                                    {abx}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {organisms.map(org => (
                            <tr key={org} className="hover:bg-gray-700/30 transition">
                                <td className="p-4 text-left font-bold text-white border-b border-gray-700 bg-gray-900/50 sticky left-0">
                                    {org}
                                </td>
                                {antibiotics.map(abx => {
                                    const cellData = matrix[org][abx];
                                    if (!cellData) {
                                        return <td key={abx} className="p-3 border-b border-gray-700 text-gray-600">-</td>;
                                    }

                                    const val = viewMode === 'current' ? cellData.current : cellData.predicted;
                                    const history = cellData.history || [];

                                    return (
                                        <td key={abx} className="p-1 border-b border-gray-700">
                                            <div className={`py-1 px-1 rounded border ${getColorClass(val)} font-mono flex flex-col items-center justify-center h-16`}>
                                                <span className="text-sm font-bold">{val.toFixed(0)}%</span>
                                                {viewMode === 'current' && history.length > 1 && (
                                                    <div className="mt-1 opacity-80 hover:opacity-100">
                                                        <Sparkline data={history} />
                                                    </div>
                                                )}
                                                {viewMode === 'predicted' && (
                                                    <span className="text-[10px] mt-1 text-purple-200 opacity-70">
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

            <div className="mt-4 flex gap-4 text-xs text-gray-400 justify-end">
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-green-900/40 border border-green-800 rounded"></span> Substantial (&gt;80%)
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-yellow-900/40 border border-yellow-800 rounded"></span> Moderate (60-80%)
                </div>
                <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-900/40 border border-red-800 rounded"></span> Resistant (&lt;60%)
                </div>
            </div>
        </div>
    );
};

export default AntibiogramTable;
