import React from 'react';
import { Target, ArrowRight, ShieldCheck, AlertTriangle, ArrowUpRight, Clock, Printer } from 'lucide-react';
import Barcode from 'react-barcode';
import { betaLactamService } from '../../../services/betaLactamService';

const GenerationRecommendation = ({ encounterId, inputContext, evalResult, recommendations, topFeatures, onASTRestriction, onProceedLabel }) => {
    // recommendations: array of { generation, probability, expected_success, score, stewardship_note, traffic_light }

    // Sort recommendations by score descending (already done by backend, but ensure safe order)
    const rankedRecs = [...(recommendations || [])].sort((a, b) => b.score - a.score);
    const topRec = rankedRecs[0];

    return (
        <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
            {/* Header: Top Recommendation Banner */}
            <div className="bg-gradient-to-br from-blue-900 via-slate-800 to-slate-900 rounded-2xl shadow-lg p-8 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2" />

                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 font-bold text-xs uppercase tracking-wider mb-4 border border-blue-500/30">
                            <Target className="w-4 h-4" />
                            Clinical Recommendation
                        </div>
                        <h2 className="text-3xl md:text-4xl font-black text-white mb-2">
                            {betaLactamService.getGenerationLabel(topRec?.generation)}
                        </h2>
                        <div className="flex items-center gap-4 text-slate-300 text-sm mt-3">
                            <span className="flex items-center gap-1.5">
                                <span className={`w-2 h-2 rounded-full ${topRec?.traffic_light === 'Green' ? 'bg-green-400' : topRec?.traffic_light === 'Amber' ? 'bg-amber-400' : 'bg-red-400'} animate-pulse`} />
                                {topRec?.traffic_light} Traffic Light
                            </span>
                            <span className="opacity-50">•</span>
                            <span className="flex items-center gap-1.5">
                                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                {topRec?.stewardship_note}
                            </span>
                        </div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-md rounded-xl p-5 border border-white/20 text-center shrink-0 min-w-[200px]">
                        <p className="text-blue-200 text-xs font-bold uppercase tracking-wider mb-1">
                            Estimated Clinical Success
                        </p>
                        <div className="flex items-end justify-center gap-1">
                            <span className="text-4xl font-black text-white">
                                {((topRec?.expected_success || 0) * 100).toFixed(1)}
                            </span>
                            <span className="text-lg font-bold text-blue-300 mb-1">%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recommendations Table */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 overflow-hidden">
                <div className="p-5 bg-slate-50 dark:bg-gray-800/50 border-b border-slate-100 dark:border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        Clinical Therapy Rankings
                    </h3>
                    <div className="bg-white dark:bg-gray-900 px-4 py-2 rounded-lg border border-slate-200 dark:border-white/10 shadow-sm flex items-center gap-2 print:hidden">
                        <Clock className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                        <span className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-widest">Encounter ID:</span>
                        <span className="text-sm font-black text-slate-800 dark:text-white">{encounterId}</span>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 dark:bg-gray-800/50 border-b border-slate-200 dark:border-white/10 text-xs uppercase tracking-wider text-slate-500 dark:text-gray-400">
                                <th className="px-6 py-4 font-bold">Rank</th>
                                <th className="px-6 py-4 font-bold">Generation</th>
                                <th className="px-6 py-4 font-bold">Predicted Susceptibility</th>
                                <th className="px-6 py-4 font-bold">Clinical Success</th>
                                <th className="px-6 py-4 font-bold text-right">Stewardship Note</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                            {rankedRecs.map((rec, index) => {
                                const isTop = index === 0;
                                const colors = betaLactamService.getTrafficLightColors(rec.traffic_light);

                                return (
                                    <tr key={rec.generation} className={`hover:bg-slate-50 dark:hover:bg-gray-800/50 transition-colors ${isTop ? 'bg-blue-50/30 dark:bg-blue-900/10' : ''}`}>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-sm ${isTop ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-100 dark:bg-gray-800 text-slate-500 dark:text-gray-400'
                                                }`}>
                                                {index + 1}
                                            </div>
                                        </td>

                                        <td className="px-6 py-4">
                                            <div className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                                {rec.generation === 'BL_Combo' ? 'BL/BLI Combo' : rec.generation}
                                                {isTop && <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider">Recommended</span>}
                                            </div>
                                            <div className="text-xs text-slate-500 dark:text-gray-400 mt-1">
                                                {betaLactamService.getGenerationExamples(rec.generation)}
                                            </div>
                                            {topFeatures && topFeatures[rec.generation] && (
                                                <div className="flex flex-wrap gap-1 mt-2" title="Key Clinical Relevance Factors">
                                                    {topFeatures[rec.generation].map(([feat, weight]) => {
                                                        const isPushedTowardsResistance = weight < 0; // Negative weight means lower prob of S (pushes towards Resistance)
                                                        return (
                                                            <span key={feat} className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${isPushedTowardsResistance ? 'bg-red-50 text-red-600 border-red-100' : 'bg-emerald-50 text-emerald-600 border-emerald-100'}`} title={`Influence contribution: ${weight > 0 ? '+' : ''}${weight.toFixed(3)}`}>
                                                                {feat.replace('Feature_', '').replace(/_/g, ' ')} {isPushedTowardsResistance ? '↑ Res' : '↑ Susc'}
                                                            </span>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </td>

                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${colors.badge} border ${colors.border}`}>
                                                {(rec.probability * 100).toFixed(1)}% ({rec.traffic_light})
                                            </span>
                                        </td>

                                        <td className="px-6 py-4">
                                            <div className="w-full max-w-[120px]">
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className="font-bold text-slate-700 dark:text-gray-300">{(rec.expected_success * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-slate-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${colors.dot}`}
                                                        style={{ width: `${rec.expected_success * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </td>

                                        <td className="px-6 py-4 text-right">
                                            {rec.stewardship_note === 'Preferred' ? (
                                                <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-200 dark:border-emerald-500/20">
                                                    <ArrowUpRight className="w-3 h-3" /> Preferred Use
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 px-2.5 py-1 rounded border border-amber-200 dark:border-amber-500/20">
                                                    <AlertTriangle className="w-3 h-3" /> Restricted Use
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Actions Footer */}
            <div className="flex justify-between items-center mt-6 pt-6 border-t border-slate-200 dark:border-white/10 print:hidden">
                <button
                    onClick={onASTRestriction}
                    className="flex items-center gap-2 px-6 py-2.5 text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg font-medium text-sm transition-colors"
                >
                    AST Results Available (Lock)
                </button>

                <div className="flex gap-4">
                    <button
                        onClick={() => window.print()}
                        className="flex items-center gap-2 px-6 py-3 bg-white dark:bg-gray-800 border border-slate-300 dark:border-gray-600 text-slate-700 dark:text-gray-200 rounded-lg font-bold text-sm hover:bg-slate-50 dark:hover:bg-gray-700 shadow-sm transition-all active:scale-95"
                    >
                        <Printer className="w-4 h-4" />
                        Print Report
                    </button>

                    <button
                        onClick={onProceedLabel}
                        className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-lg font-bold text-sm hover:bg-blue-700 shadow-md hover:shadow-lg transition-all active:scale-95"
                    >
                        Proceed to Lab Entry
                        <ArrowRight className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Printable Receipt View (Only visible during print) */}
            <div className="hidden print:block fixed inset-0 bg-white z-[9999] font-mono text-black">
                {/* 80mm Thermal Receipt Container */}
                <div className="w-[78mm] mx-auto p-2">

                    {/* Header */}
                    <div className="text-center pb-3 border-b-2 border-black border-dashed mb-3">
                        <h1 className="text-lg font-black uppercase leading-tight">Clinical Stewardship<br />Report</h1>
                        <p className="text-xs mt-1">Beta-Lactam Predictor</p>
                    </div>

                    {/* Barcode */}
                    <div className="flex flex-col items-center justify-center mb-4">
                        <Barcode value={encounterId} width={1.2} height={40} fontSize={12} margin={0} />
                    </div>

                    {/* Basic Info */}
                    <div className="text-xs space-y-1.5 border-b-2 border-black border-dashed pb-3 mb-3">
                        <div className="flex justify-between">
                            <span>Date:</span> <span className="font-bold">{new Date().toLocaleDateString()}</span>
                        </div>
                        {inputContext && (
                            <>
                                <div className="flex justify-between">
                                    <span>Age/Gen:</span> <span className="font-bold">{inputContext.Age}Y, {inputContext.Gender}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Ward:</span> <span className="font-bold">{inputContext.Ward}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Sample:</span> <span className="font-bold">{inputContext.Sample_Type}</span>
                                </div>
                                <div className="flex flex-col mt-1">
                                    <span>Organism:</span>
                                    <span className="font-bold leading-tight">{inputContext.Organism?.replace('_', ' ')}</span>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Recommendation */}
                    <div className="text-center mb-3">
                        <div className="text-[10px] uppercase font-bold mb-1">Primary Recommendation</div>
                        <div className="text-lg font-black uppercase border-y-2 border-black py-1">
                            {betaLactamService.getGenerationLabel(topRec?.generation)}
                        </div>
                        <div className="text-xs font-bold mt-1">
                            {((topRec?.expected_success || 0) * 100).toFixed(1)}% Est. Success
                        </div>
                    </div>

                    {/* Stewardship Note */}
                    <div className="text-[10px] text-center italic border-b-2 border-black border-dashed pb-3 mb-3 px-1 leading-tight font-bold">
                        Note: {topRec?.stewardship_note}
                    </div>

                    {/* Footer */}
                    <div className="text-[9px] text-center leading-tight">
                        Generated by AI-Assisted<br />Clinical Surveillance.<br />
                        <span className="font-bold">Attach to Patient File.</span><br />
                        Scan Barcode at Lab Entry.
                    </div>

                </div>
            </div>
        </div>
    );
};

export default GenerationRecommendation;
