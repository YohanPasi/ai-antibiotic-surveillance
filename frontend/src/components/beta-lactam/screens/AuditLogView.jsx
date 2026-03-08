import React, { useState, useEffect } from 'react';
import { ShieldCheck, History, AlertOctagon, User, BookOpen, Layers, CheckCircle2, AlertTriangle } from 'lucide-react';
import { betaLactamService } from '../../../services/betaLactamService';

const AuditLogView = ({ onClose }) => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await betaLactamService.getAuditLogs();
                setLogs(response.logs || []);
            } catch (err) {
                console.error("Failed to fetch audit logs", err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    // Helper to format date
    const formatDate = (isoString) => {
        const d = new Date(isoString);
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col border border-slate-200 dark:border-white/10 animate-in zoom-in-95 slide-in-from-bottom-4 duration-300"
                onClick={e => e.stopPropagation()}
            >

                {/* Header */}
                <div className="px-8 py-6 border-b border-slate-100 dark:border-white/5 flex items-center justify-between bg-white dark:bg-gray-900 rounded-t-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500"></div>
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl shadow-inner dark:shadow-none">
                            <History className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">System Governance & Audit Trail</h2>
                            <p className="text-sm text-slate-500 dark:text-gray-400 font-medium mt-0.5">Immutable record of Beta-Lactam Susceptibility Assessments and clinical overrides</p>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            onClose();
                        }}
                        className="relative z-50 p-2 bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-gray-400 hover:bg-slate-200 dark:hover:bg-white/10 hover:text-slate-800 dark:hover:text-white rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300 dark:focus:ring-white/20"
                    >
                        <svg className="w-5 h-5 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6 bg-slate-50 dark:bg-gray-950 px-8 relative">
                    {loading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                            <div className="w-8 h-8 border-4 border-slate-300 dark:border-gray-700 border-t-slate-800 dark:border-t-white rounded-full animate-spin"></div>
                            <p className="text-sm font-bold text-slate-500 dark:text-gray-400 uppercase tracking-widest animate-pulse">Retrieving Logs</p>
                        </div>
                    ) : logs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-2">
                            <BookOpen className="w-12 h-12 opacity-20" />
                            <p>No governance events recorded yet.</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto bg-white dark:bg-gray-900 border border-slate-200 dark:border-white/10 rounded-xl shadow-sm">
                            <table className="w-full text-left border-collapse text-sm">
                                <thead>
                                    <tr className="bg-slate-50 dark:bg-gray-800 border-b border-slate-200 dark:border-white/10 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-gray-400">
                                        <th className="px-6 py-4">Timestamp</th>
                                        <th className="px-6 py-4">Encounter / Pathogen</th>
                                        <th className="px-6 py-4">Risk Level</th>
                                        <th className="px-6 py-4">Clinical Recommendation</th>
                                        <th className="px-6 py-4 text-center">Susceptibility Spectrum</th>
                                        <th className="px-6 py-4">Override Status</th>
                                        <th className="px-6 py-4">Version & Flags</th>
                                    </tr>

                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {logs.map((log) => {
                                        return (
                                            <tr key={log.id} className="hover:bg-slate-50/80 dark:hover:bg-white/5 transition-all group">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-xs font-medium text-slate-600 dark:text-gray-300">
                                                        {new Date(log.timestamp).toLocaleDateString()}
                                                    </div>
                                                    <div className="text-[10px] font-bold text-slate-400 dark:text-gray-500 font-mono mt-0.5">
                                                        {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </div>
                                                </td>

                                                <td className="px-6 py-4">
                                                    <div className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{log.encounter_id}</div>
                                                    <div className="text-xs font-medium text-slate-500 dark:text-gray-400 mt-0.5 flex items-center gap-1.5">
                                                        <span className="truncate max-w-[120px]" title={log.organism}>{log.organism?.replace(/_/g, ' ')}</span>
                                                        <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-gray-600"></span>
                                                        <span>{log.ward}</span>
                                                    </div>
                                                </td>

                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide border shadow-sm ${log.risk_group === 'High' ? 'bg-red-50 text-red-700 border-red-200' :
                                                        log.risk_group === 'Moderate' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                                            'bg-emerald-50 text-emerald-700 border-emerald-200'
                                                        }`}>
                                                        {log.risk_group === 'High' && <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1.5 animate-pulse"></span>}
                                                        {log.risk_group || 'Low'} Risk
                                                    </span>
                                                </td>

                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-2">
                                                        <div className="p-1.5 bg-indigo-50 dark:bg-indigo-500/10 rounded-lg text-indigo-600 dark:text-indigo-400 shadow-sm border border-indigo-100 dark:border-indigo-500/20">
                                                            <Layers className="w-4 h-4" />
                                                        </div>
                                                        <div>
                                                            <div className="text-sm font-bold text-slate-800 dark:text-gray-200">
                                                                {betaLactamService.getGenerationLabel(log.top_generation_recommendation)}
                                                            </div>
                                                            <div className="text-[11px] font-medium text-slate-500 dark:text-gray-400 mt-0.5">
                                                                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{((parseFloat(log.predicted_success_probability || 0)) * 100).toFixed(1)}%</span> success est.
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>

                                                <td className="px-6 py-4">
                                                    {(() => {
                                                        try {
                                                            const spec = typeof log.predicted_beta_lactam_spectrum === 'string' ? JSON.parse(log.predicted_beta_lactam_spectrum) : (log.predicted_beta_lactam_spectrum || {});
                                                            const gens = ['Gen1', 'Gen2', 'Gen3', 'Gen4', 'Carbapenem', 'BL_Combo'];
                                                            return (
                                                                <div className="flex items-center justify-center gap-1.5 bg-slate-50 dark:bg-gray-800 py-1.5 px-3 rounded-xl border border-slate-200 dark:border-white/5 w-max mx-auto shadow-inner dark:shadow-none">
                                                                    {gens.map(gen => {
                                                                        const tl = spec[gen]?.traffic_light || 'Red';
                                                                        return (
                                                                            <div key={gen} title={`${gen}: ${tl}`} className={`w-2.5 h-2.5 rounded-full ring-2 ring-white dark:ring-gray-900 shadow-sm ${tl === 'Green' ? 'bg-emerald-500' : tl === 'Amber' ? 'bg-amber-400' : 'bg-red-500'}`} />
                                                                        );
                                                                    })}
                                                                </div>
                                                            );
                                                        } catch (e) {
                                                            return <span className="text-xs text-slate-400">Error Parsing</span>;
                                                        }
                                                    })()}
                                                </td>

                                                <td className="px-6 py-4">
                                                    {log.clinician_override ? (
                                                        <div className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-1.5 rounded-lg border border-amber-200 shadow-sm cursor-help transition-transform hover:scale-105" title={log.override_reason}>
                                                            <AlertOctagon className="w-3.5 h-3.5" />
                                                            <span>Overridden</span>
                                                        </div>
                                                    ) : (
                                                        <div className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-100 shadow-sm transition-transform hover:scale-105">
                                                            <CheckCircle2 className="w-3.5 h-3.5" />
                                                            <span>Followed</span>
                                                        </div>
                                                    )}
                                                </td>

                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1.5">
                                                        <span className="text-[10px] font-mono font-bold text-slate-500 dark:text-gray-400 bg-slate-100 dark:bg-gray-800 px-2 py-0.5 rounded-md w-max border border-slate-200 dark:border-white/5 shadow-sm">
                                                            {log.model_version?.substring(0, 15) || 'Unknown'}
                                                        </span>
                                                        {log.ood_detected && (
                                                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-orange-700 dark:text-orange-400 bg-orange-50 dark:bg-orange-500/10 px-2 py-0.5 rounded-md w-max border border-orange-200 dark:border-orange-500/20 shadow-sm" title="Rare Clinical Presentation">
                                                                <AlertTriangle className="w-3 h-3" /> Rare Case
                                                            </span>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-slate-900 text-slate-400 text-xs border-t border-slate-800 flex justify-between items-center rounded-b-2xl">
                    <div className="flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Access Logged: Clinician Auto-Tracking Active
                    </div>
                    <div>
                        <span className="font-bold text-white tracking-widest">{logs.length}</span> EVENTS SHOWN
                    </div>
                </div>

            </div>
        </div>
    );
};

export default AuditLogView;
