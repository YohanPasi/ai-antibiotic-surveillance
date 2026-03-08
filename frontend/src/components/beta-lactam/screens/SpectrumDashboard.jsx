import React from 'react';
import { ShieldAlert, AlertTriangle, Users, Target, Activity, CheckCircle, Info } from 'lucide-react';
import { betaLactamService } from '../../../services/betaLactamService';

const SpectrumDashboard = ({ inputs, result, onNext }) => {
    // result expects: spectrum (dict), risk_group, ood_warning, top_generation_recommendation
    const { spectrum, risk_group, ood_warning } = result;

    // Filter to only show the core beta-lactam generations
    const displayGenerations = ['Gen1', 'Gen2', 'Gen3', 'Gen4', 'Carbapenem', 'BL_Combo'];

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* OOD Warning Banner */}
            {ood_warning && (
                <div className="bg-amber-50 dark:bg-amber-500/10 border-l-4 border-amber-500 dark:border-amber-500/50 p-4 rounded-r-xl flex gap-3 shadow-sm animate-in fade-in slide-in-from-top-2">
                    <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-bold text-amber-800 dark:text-amber-400">
                            Rare Clinical Presentation Alert
                        </h4>
                        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                            The patient's initial clinical features (e.g. Age {inputs.Age}) present a rare profile based on historical data.
                            Susceptibility assessments may have reduced certainty. Proceed with caution.
                        </p>
                    </div>
                </div>
            )}

            {/* Top Stat Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Context Card */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 p-5 flex items-start gap-4">
                    <div className="p-3 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-gray-300 rounded-lg shrink-0">
                        <Users className="w-6 h-6" />
                    </div>
                    <div>
                        <p className="text-xs font-bold tracking-wider text-slate-400 dark:text-gray-500 uppercase mb-1">Patient Context</p>
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white">
                            {inputs.Age}y {inputs.Gender} • {inputs.Ward}
                        </h3>
                        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">
                            <span className="font-medium text-slate-700 dark:text-gray-300">{inputs.Sample_Type}</span> •
                            Organism: <span className="font-medium text-slate-700 dark:text-gray-300">{inputs.Organism.replace('_', ' ')}</span>
                        </p>
                    </div>
                </div>

                {/* Overall Risk Profile */}
                <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 p-5 flex items-center justify-between">
                    <div>
                        <p className="text-xs font-bold tracking-wider text-slate-400 dark:text-gray-500 uppercase mb-1">Resistance Risk Profile</p>
                        <div className="flex items-center gap-3">
                            <h3 className="text-2xl font-black text-slate-800 dark:text-white">
                                {risk_group || 'Unknown'} Risk
                            </h3>
                            {risk_group === 'High' && <ShieldAlert className="w-6 h-6 text-red-500" />}
                            {risk_group === 'Moderate' && <AlertTriangle className="w-6 h-6 text-amber-500" />}
                            {risk_group === 'Low' && <CheckCircle className="w-6 h-6 text-green-500" />}
                        </div>
                        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Based on worst-case susceptibility assessment</p>
                    </div>
                </div>
            </div>

            {/* Spectrum Grid */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 overflow-hidden">
                <div className="p-5 bg-slate-50 dark:bg-gray-800/50 border-b border-slate-100 dark:border-white/5 flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <Target className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            Susceptibility Spectrum Assessment
                        </h3>
                        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">
                            Estimated susceptibility by beta-lactam generation
                        </p>
                    </div>
                </div>

                <div className="p-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                        {displayGenerations.map(gen => {
                            const data = spectrum[gen] || { probability: 0, traffic_light: 'Red' };
                            const colors = betaLactamService.getTrafficLightColors(data.traffic_light);
                            const percent = (data.probability * 100).toFixed(1);

                            return (
                                <div key={gen} className={`p-4 rounded-xl border ${colors.border} ${colors.bg} relative overflow-hidden transition-all hover:shadow-md`}>
                                    <div className="flex justify-between items-start mb-2 relative z-10">
                                        <h4 className={`font-bold ${colors.text}`}>
                                            {gen === 'BL_Combo' ? 'BL/BLI Combo' : gen}
                                        </h4>
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${colors.badge}`}>
                                            {data.traffic_light}
                                        </span>
                                    </div>

                                    <div className="relative z-10">
                                        <div className="flex items-end gap-1">
                                            <span className={`text-3xl font-black ${colors.text}`}>{percent}</span>
                                            <span className={`text-sm font-bold mb-1 ${colors.text}`}>%</span>
                                        </div>
                                        <p className={`text-xs mt-1 opacity-80 ${colors.text}`}>
                                            estimated susceptibility
                                        </p>
                                    </div>

                                    {/* Progress Bar Background */}
                                    <div className="absolute bottom-0 left-0 w-full h-1 bg-black/5">
                                        <div
                                            className={`h-full ${colors.dot}`}
                                            style={{ width: `${percent}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="px-6 py-4 bg-slate-50 dark:bg-gray-800/50 border-t border-slate-100 dark:border-white/5 flex items-start gap-2 text-xs text-slate-500 dark:text-gray-400">
                    <Info className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" />
                    <p>
                        Green indicates ≥70% probability of susceptibility. Amber indicates 40-69%. Red indicates &lt;40%.
                        These thresholds are governed by the antimicrobial stewardship committee.
                    </p>
                </div>
            </div>

            {/* Next Step Button */}
            <div className="flex justify-end">
                <button
                    onClick={onNext}
                    className="flex items-center gap-2 px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg font-bold text-sm hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm active:scale-95"
                >
                    View Recommended Generation
                    <Activity className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
};

export default SpectrumDashboard;
