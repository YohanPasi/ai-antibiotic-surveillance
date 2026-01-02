import React, { useState, useEffect } from 'react';
import HistoricalChart from './HistoricalChart';
import { XCircle } from 'lucide-react';
import AntibiogramTable from './AntibiogramTable';

const WardDetail = ({ wardId, goBack }) => {
    const [details, setDetails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTarget, setSelectedTarget] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [analysisLoading, setAnalysisLoading] = useState(false);

    useEffect(() => {
        fetch(`http://localhost:8000/api/ward/${wardId}/status`)
            .then(res => res.json())
            .then(data => {
                setDetails(data.monitored_targets);
                setLoading(false);
            })
            .catch(err => console.error(err));
    }, [wardId]);

    const handleRowClick = (organism, antibiotic) => {
        setSelectedTarget({ organism, antibiotic });
        setAnalysisLoading(true);
        fetch(`http://localhost:8000/api/analysis/target?ward=${wardId}&organism=${organism}&antibiotic=${antibiotic}`)
            .then(res => res.json())
            .then(data => {
                // Merge History and Baseline for Chart
                const merged = data.history.map((h, i) => ({
                    ...h,
                    expected_s: data.baseline[i]?.expected_s
                }));
                setAnalysisData({ history: merged, forecast: data.forecast });
                setAnalysisLoading(false);
            })
            .catch(err => {
                console.error(err);
                setAnalysisLoading(false);
            });
    };

    if (loading) return <div className="text-white">Loading Ward Data...</div>;

    return (
        <div className="space-y-6 relative">
            <button onClick={goBack} className="text-gray-400 hover:text-white mb-4">← Back to Overview</button>

            {/* Ward-Specific Antibiogram Matrix */}
            <AntibiogramTable wardId={wardId} />

            {/* Analysis Modal/Overlay */}
            {selectedTarget && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <div className="p-4 border-b border-gray-800 flex justify-between items-center sticky top-0 bg-gray-900 z-10">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    📈 Sensitivity Pattern Analysis: <span className="text-blue-400">{selectedTarget.organism}</span>
                                </h3>
                                <p className="text-sm text-gray-400">Antibiotic: {selectedTarget.antibiotic} | Ward: {wardId}</p>
                            </div>
                            <button onClick={() => { setSelectedTarget(null); setAnalysisData(null); }} className="text-gray-400 hover:text-white">
                                <XCircle size={24} />
                            </button>
                        </div>

                        <div className="p-6">
                            <HistoricalChart
                                data={analysisData?.history}
                                prediction={analysisData?.forecast}
                                loading={analysisLoading}
                            />

                            <div className="mt-6 bg-gray-800 p-4 rounded border border-gray-700">
                                <h4 className="font-bold text-yellow-500 mb-2">⚠️ Interpretation Note</h4>
                                <p className="text-sm text-gray-300">
                                    The <strong>Forecast Point</strong> (Hollow Circle) indicates the predicted trajectory for next week.
                                    Compare it against the <strong>Statistical Baseline</strong> (Dashed Line).
                                    Significant deviation suggests actionable resistance erosion.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h2 className="text-2xl font-bold text-white mb-2">Ward {wardId} Detail</h2>
                <p className="text-gray-400 text-sm mb-6">Click on any row to view Time-Series Analysis</p>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="text-gray-400 border-b border-gray-700">
                                <th className="p-3">Organism</th>
                                <th className="p-3">Antibiotic</th>
                                <th className="p-3">Current S%</th>
                                <th className="p-3">Baseline</th>
                                <th className="p-3">Forecast</th>
                                <th className="p-3">Trend</th>
                                <th className="p-3">Status</th>
                                <th className="p-3">Stewardship Domain</th>
                            </tr>
                        </thead>
                        <tbody>
                            {details.map((row, idx) => (
                                <tr
                                    key={idx}
                                    onClick={() => handleRowClick(row.organism, row.antibiotic)}
                                    className="border-b border-gray-700 hover:bg-gray-700 cursor-pointer transition"
                                >
                                    <td className="p-3 font-medium text-white">{row.organism}</td>
                                    <td className="p-3 text-gray-300">{row.antibiotic}</td>
                                    <td className="p-3 font-bold text-white">{row.current_s.toFixed(1)}%</td>
                                    <td className="p-3 text-gray-400">{row.baseline_s.toFixed(1)}%</td>
                                    <td className="p-3 text-blue-300">{row.forecast_s.toFixed(1)}%</td>
                                    <td className="p-3">
                                        <div className="flex items-center gap-2">
                                            <span className={`font-bold text-lg ${row.trend === '↓' ? 'text-red-500' : 'text-green-500'}`}>
                                                {row.trend}
                                            </span>
                                            <span className="text-xs bg-gray-700 px-2 py-1 rounded text-gray-300 hover:bg-blue-600 transition">View Graph</span>
                                        </div>
                                    </td>
                                    <td className="p-3">
                                        <span className={`w-3 h-3 inline-block rounded-full mr-2 
                        ${row.status === 'red' || row.status === 'critical' ? 'bg-red-500 shadow-red-500 shadow-md' :
                                                row.status === 'amber' || row.status === 'amber-high' ? 'bg-yellow-500 shadow-yellow-500 shadow-md' : 'bg-green-500'}`}>
                                        </span>
                                        <span className="capitalize text-gray-300">{row.status}</span>
                                    </td>
                                    <td className="p-3 text-gray-300 italic">{row.stewardship}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default WardDetail;
