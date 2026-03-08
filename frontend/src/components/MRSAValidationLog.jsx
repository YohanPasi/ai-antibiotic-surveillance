import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const BAND_STYLES = {
    RED: { bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-300 dark:border-red-600', text: 'text-red-600 dark:text-red-400' },
    AMBER: { bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-300 dark:border-amber-500', text: 'text-amber-600 dark:text-amber-400' },
    GREEN: { bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-300 dark:border-green-600', text: 'text-green-600 dark:text-green-400' },
};

const MRSAValidationLog = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => { fetchLogs(); }, []);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/api/mrsa/validation-logs`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) setLogs(await res.json());
        } catch (err) {
            console.error('Failed to fetch validation logs', err);
        } finally {
            setLoading(false);
        }
    };

    const filtered = logs.filter(l =>
        !search ||
        l.ward?.toLowerCase().includes(search.toLowerCase()) ||
        l.sample_type?.toLowerCase().includes(search.toLowerCase()) ||
        l.consensus_band?.toLowerCase().includes(search.toLowerCase())
    );

    const correct = logs.filter(l => l.consensus_correct).length;
    const accuracy = logs.length > 0 ? Math.round((correct / logs.length) * 100) : null;

    return (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">

            {/* Header */}
            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex flex-wrap items-center gap-4">
                <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">Screening Accuracy History</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-0.5">Verified against confirmed Cefoxitin (FOX) disc test results</p>
                </div>
                <div className="ml-auto flex items-center gap-3">
                    {/* Stats */}
                    {accuracy !== null && (
                        <div className="flex items-center gap-3 mr-1">
                            <span className="text-xs text-slate-500 dark:text-slate-500">{logs.length} records</span>
                            <span className="text-xs font-semibold text-green-600 dark:text-green-400">{accuracy}% accurate</span>
                        </div>
                    )}
                    {/* Search */}
                    <div className="relative">
                        <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <input
                            type="text"
                            placeholder="Search..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-800 dark:text-slate-300 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-36"
                        />
                    </div>
                    {/* Refresh */}
                    <button onClick={fetchLogs} className="p-1.5 rounded-lg text-slate-500 dark:text-slate-500 hover:text-slate-800 dark:text-slate-300 hover:bg-slate-100 dark:bg-slate-700 transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Content */}
            {loading ? (
                <div className="flex items-center justify-center py-12 gap-2 text-slate-500 dark:text-slate-500 text-sm">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Loading...
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-100 dark:bg-slate-700/50">
                            <tr>
                                {['Date', 'Ward', 'Sample type', 'Screening result', 'Cefoxitin disc', 'True result', 'Correct?'].map(h => (
                                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-600 dark:text-slate-400">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-4 py-10 text-center text-slate-500 dark:text-slate-500 text-sm">
                                        {search ? 'No matching records found.' : 'No confirmed cultures yet.'}
                                        <br />
                                        <span className="text-xs">Records appear when Cefoxitin results are confirmed for Staph. aureus cultures.</span>
                                    </td>
                                </tr>
                            ) : (
                                filtered.map((log, idx) => {
                                    const b = BAND_STYLES[log.consensus_band] || {};
                                    return (
                                        <tr key={log.id} className={`border-t border-slate-200 dark:border-slate-700 ${idx % 2 === 1 ? 'bg-slate-50 dark:bg-slate-700/20' : ''} hover:bg-slate-100 dark:hover:bg-slate-700/40 transition-colors`}>
                                            <td className="px-4 py-3 text-slate-600 dark:text-slate-400 font-mono text-xs whitespace-nowrap">
                                                {new Date(log.validation_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' })}
                                            </td>
                                            <td className="px-4 py-3 text-slate-800 dark:text-slate-300">{log.ward || '—'}</td>
                                            <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{log.sample_type || '—'}</td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${b.bg} ${b.border} ${b.text}`}>
                                                    {log.consensus_band}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 font-mono font-semibold">
                                                <span className={log.cefoxitin_result === 'R' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}>
                                                    {log.cefoxitin_result}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`text-xs font-medium ${log.actual_mrsa ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                                                    {log.actual_mrsa ? 'MRSA' : 'MSSA'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                {log.consensus_correct ? (
                                                    <span className="text-green-600 dark:text-green-400 text-xs font-medium">✓ Yes</span>
                                                ) : (
                                                    <span className="text-red-600 dark:text-red-400 text-xs font-medium">✗ Missed</span>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default MRSAValidationLog;
