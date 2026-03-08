import React, { useState, useEffect } from 'react';
import { Target, ArrowRight, ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2, History } from 'lucide-react';
import { betaLactamService } from '../../../services/betaLactamService';

const PostASTReview = ({ encounterId, empiricGeneration, onComplete }) => {
    const [labData, setLabData] = useState(null);
    const [reviewStatus, setReviewStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [auditState, setAuditState] = useState(''); // 'pending', 'saving', 'saved'

    const [actualEmpiricGen, setActualEmpiricGen] = useState(empiricGeneration);

    useEffect(() => {
        const fetchAndAnalyze = async () => {
            try {
                let genToUse = empiricGeneration;
                if (!genToUse) {
                    const record = await betaLactamService.getEncounter(encounterId);
                    if (record?.result?.top_generation_recommendation) {
                        genToUse = record.result.top_generation_recommendation;
                        setActualEmpiricGen(genToUse);
                    } else {
                        throw new Error("Could not find empiric generation for this encounter.");
                    }
                }

                // 1. Fetch confirmed lab results (returns flat 'results' dict)
                const labRes = await betaLactamService.getLabResults(encounterId);
                setLabData(labRes.results || {});

                // 2. Run Stewardship Rules via backend
                const feedback = await betaLactamService.getPostASTReview(genToUse, labRes.results || {});
                setReviewStatus(feedback);
            } catch (err) {
                console.error("Failed to fetch POST-AST analysis:", err);
            } finally {
                setLoading(false);
            }
        };

        if (encounterId) {
            fetchAndAnalyze();
        }
    }, [encounterId, empiricGeneration]);

    const handleAcknowledge = async () => {
        setAuditState('saving');
        try {
            await betaLactamService.logDecision({
                encounter_id: encounterId,
                user_id: 'auto-steward-sys',
                model_version: 'post-ast-rules-v1',
                generation_recommended: reviewStatus?.action,
                decision: 'ACKNOWLEDGED_POST_AST',
                reason_code: reviewStatus?.message,
                selected_generation: actualEmpiricGen
            });
            setAuditState('saved');
            setTimeout(() => onComplete(), 1500);
        } catch (e) {
            console.error("Audit log failed", e);
            setAuditState('error');
        }
    };

    if (loading) {
        return (
            <div className="max-w-3xl mx-auto p-12 flex flex-col items-center justify-center space-y-4">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-500 font-medium animate-pulse">Running Confirmatory Stewardship Analysis...</p>
            </div>
        );
    }

    if (!labData || !reviewStatus) {
        return (
            <div className="max-w-3xl mx-auto p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-slate-800">No Post-AST Data Available</h3>
                <p className="text-slate-500 mt-2 text-sm">Waiting for confirmed lab results to perform stewardship review.</p>
            </div>
        );
    }

    const isRed = reviewStatus.alert_level === 'RED';
    const isAmber = reviewStatus.alert_level === 'YELLOW' || reviewStatus.alert_level === 'AMBER';
    const isGreen = reviewStatus.alert_level === 'GREEN';

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
            {/* Alert Header */}
            <div className={`rounded-xl shadow-lg p-6 border-l-8 flex items-start gap-4 transition-all ${isRed ? 'bg-red-50 border-red-500 text-red-900' :
                isAmber ? 'bg-amber-50 border-amber-500 text-amber-900' :
                    'bg-emerald-50 border-emerald-500 text-emerald-900'
                }`}>
                <div className="shrink-0 mt-1">
                    {isRed ? <AlertOctagon className="w-8 h-8 text-red-500" /> :
                        isAmber ? <AlertTriangle className="w-8 h-8 text-amber-500" /> :
                            <ShieldCheck className="w-8 h-8 text-emerald-500" />}
                </div>
                <div className="flex-1">
                    <div className="text-xs font-black tracking-wider uppercase opacity-70 mb-1">
                        Post-AST Stewardship Directive
                    </div>
                    <h2 className="text-2xl font-black mb-2 tracking-tight">
                        {(reviewStatus.action || 'Review Complete').replace(/_/g, ' ')}
                    </h2>
                    <p className={`font-medium text-lg leading-relaxed ${isRed ? 'text-red-800' : isAmber ? 'text-amber-800' : 'text-emerald-800'
                        }`}>
                        {reviewStatus.message}
                    </p>
                </div>
            </div>

            {/* Context Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Empiric Selection (Day-0)</div>
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-slate-100 rounded-lg text-slate-500">
                            <History className="w-5 h-5" />
                        </div>
                        <div>
                            <span className="block text-sm text-slate-500 font-medium">Assessed Generation</span>
                            <span className="block text-lg font-black text-slate-800">
                                {betaLactamService.getGenerationLabel(actualEmpiricGen)}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Confirmed Lab Panel (Day-3)</div>
                    <div className="flex flex-wrap gap-2">
                        {Object.entries(labData).map(([drug, val]) => (
                            <span key={drug} className={`text-xs font-bold px-2 py-1 rounded shadow-sm border ${val === 'S' ? 'bg-green-100 text-green-800 border-green-200' :
                                val === 'I' ? 'bg-amber-100 text-amber-800 border-amber-200' :
                                    'bg-red-100 text-red-800 border-red-200'
                                }`}>
                                {drug}: {val}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Acknowledge Footer */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 flex items-center justify-between mt-8">
                <div className="text-sm font-medium text-slate-500">
                    Review completed. Action required based on directive above.
                </div>
                <button
                    onClick={handleAcknowledge}
                    disabled={auditState === 'saving' || auditState === 'saved'}
                    className={`flex items-center gap-2 px-8 py-3 rounded-lg font-bold text-sm transition-all shadow-sm ${auditState === 'saving' ? 'bg-slate-300 text-slate-500 cursor-not-allowed' :
                        auditState === 'saved' ? 'bg-emerald-500 text-white shadow-md' :
                            'bg-slate-900 text-white hover:bg-slate-800 active:scale-95'
                        }`}
                >
                    {auditState === 'saving' ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                            Logging Audit...
                        </>
                    ) : auditState === 'saved' ? (
                        <>
                            <CheckCircle2 className="w-4 h-4" />
                            Acknowledged
                        </>
                    ) : (
                        <>
                            Acknowledge Directive
                            <ArrowRight className="w-4 h-4" />
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};

export default PostASTReview;
