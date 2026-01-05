
import React, { useState } from 'react';
import { CaseRegistration } from './screens/CaseRegistration';
import { RiskDashboard } from './screens/RiskDashboard';
import { RecommendationEngine } from './screens/RecommendationEngine';
import { SystemStatusFooter } from './SystemStatusFooter';
import { esblService } from '../../services/esblService';

import { PostASTReview } from './screens/PostASTReview';
import { AuditLogView } from './screens/AuditLogView';

const STEPS = {
    REGISTRATION: 'REGISTRATION',
    RISK_DASHBOARD: 'RISK_DASHBOARD',
    RECOMMENDATION: 'RECOMMENDATION',
    POST_AST: 'POST_AST'
};

export const ESBLModule = () => {
    const [currentStep, setCurrentStep] = useState(STEPS.REGISTRATION);
    const [caseContext, setCaseContext] = useState({});
    const [evaluationResult, setEvaluationResult] = useState(null);
    const [astAvailable, setAstAvailable] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showAuditLogs, setShowAuditLogs] = useState(false);

    // Workflow Handlers
    const handleRegistrationComplete = async (inputs) => {
        setLoading(true);
        setError(null);
        try {
            // 1. Call Main Engine
            const result = await esblService.evaluateCase(inputs, false);

            setCaseContext(inputs);
            setEvaluationResult(result);
            setCurrentStep(STEPS.RISK_DASHBOARD);

        } catch (err) {
            console.error(err);
            setError(err.message || "Failed to evaluate case.");
        } finally {
            setLoading(false);
        }
    };

    const handleASTUpload = () => {
        // Simulate AST Result Availability -> Triggers Lock & Post-AST Mode
        setAstAvailable(true);
        setCurrentStep(STEPS.POST_AST);
        alert("AST Results Uploaded. Switching to Confirmatory Mode.");
    };

    // Render Logic
    return (
        <div className="flex flex-col h-full bg-slate-50 relative overflow-hidden">
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                    {/* Header Section */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-6 border-b border-slate-200">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">ESBL <span className="text-blue-600">Assistant</span></h1>
                            <p className="text-sm text-slate-500 mt-1">AI-Powered Clinical Decision Support System</p>
                        </div>

                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setShowAuditLogs(true)}
                                className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-transparent hover:bg-white hover:border-slate-200 transition-all"
                            >
                                <span>🛡️</span> Governance Logs
                            </button>

                            {astAvailable && (
                                <div className="mt-4 md:mt-0 flex items-center gap-2 bg-red-50 text-red-700 px-4 py-2 rounded-lg border border-red-100 shadow-sm animate-pulse">
                                    <span className="w-2 h-2 bg-red-600 rounded-full"></span>
                                    <span className="font-semibold text-sm">Confirmatory Mode Active</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-50 text-red-700 p-4 rounded mb-4 border border-red-200">
                            ⚠️ Error: {error}
                        </div>
                    )}

                    {/* Workflow Steps */}
                    {currentStep === STEPS.REGISTRATION && (
                        <CaseRegistration
                            onNext={handleRegistrationComplete}
                            isLoading={loading}
                        />
                    )}

                    {currentStep === STEPS.RISK_DASHBOARD && (
                        <RiskDashboard
                            inputs={caseContext}
                            riskData={evaluationResult?.risk}
                            warnings={evaluationResult?.warnings}
                            onNext={() => setCurrentStep(STEPS.RECOMMENDATION)}
                            onBack={() => setCurrentStep(STEPS.REGISTRATION)}
                        />
                    )}

                    {currentStep === STEPS.RECOMMENDATION && (
                        <RecommendationEngine
                            recommendations={evaluationResult?.recommendations}
                            riskGroup={evaluationResult?.risk?.group}
                            onOverride={(decision) => console.log("Decision Logged", decision)}
                            astLocked={astAvailable}
                        />
                    )}

                    {currentStep === STEPS.POST_AST && (
                        <PostASTReview
                            onReset={() => {
                                setAstAvailable(false);
                                setCurrentStep(STEPS.REGISTRATION);
                                setCaseContext({});
                            }}
                        />
                    )}

                </div>

                {/* Footer / Governance Bar */}
                <SystemStatusFooter
                    versions={evaluationResult?.metadata}
                    astLocked={astAvailable}
                    onSimulateAST={handleASTUpload}
                />
            </div>

            {/* Audit Log Modal Overlay */}
            {showAuditLogs && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="w-full max-w-5xl h-[80vh]">
                        <AuditLogView onClose={() => setShowAuditLogs(false)} />
                    </div>
                </div>
            )}
        </div>
    );
};
