import React, { useState } from 'react';
import { Shield, Activity, Beaker, FileCheck, FileSignature, AlertCircle } from 'lucide-react';
import { betaLactamService } from '../../services/betaLactamService';

import CaseRegistration from './screens/CaseRegistration';
import SpectrumDashboard from './screens/SpectrumDashboard';
import GenerationRecommendation from './screens/GenerationRecommendation';
import LabEntryForm from './screens/LabEntryForm';
import PostASTReview from './screens/PostASTReview';
import AuditLogView from './screens/AuditLogView';


const BetaLactamModule = () => {
    // Current active step
    const [currentStep, setCurrentStep] = useState(1);

    // Core State
    const [encounterId, setEncounterId] = useState(`ENC-${Math.random().toString(36).substr(2, 6).toUpperCase()}`);
    const [inputContext, setInputContext] = useState(null);
    const [evalResult, setEvalResult] = useState(null);
    const [showAuditLogs, setShowAuditLogs] = useState(false);
    const [error, setError] = useState(null);

    const steps = [
        { id: 1, name: 'Registration', icon: Activity },
        { id: 2, name: 'Spectrum', icon: Shield },
        { id: 3, name: 'Recommendations', icon: FileCheck },
        { id: 4, name: 'AST Lab', icon: Beaker },
        { id: 5, name: 'Post-AST Review', icon: FileSignature }
    ];

    // ── Handlers ─────────────────────────────────────────────────────────────

    // Screen 1 -> Screen 2
    const handleRegistrationComplete = async (inputs) => {
        try {
            setError(null);
            setInputContext({ ...inputs, id: encounterId });

            // 1. Evaluate Case
            const result = await betaLactamService.evaluateCase(inputs, false);
            setEvalResult(result);

            // 2. Save Encounter automatically
            await betaLactamService.saveEncounter(encounterId, { inputs: { ...inputs, id: encounterId }, result });

            setCurrentStep(2);
        } catch (err) {
            setError(err.message || 'Failed to evaluate case. Ensure backend is running.');
            console.error(err);
        }
    };

    // Screen 3 -> Screen 4 (AST Restriction override/lock)
    const handleASTRestriction = async () => {
        try {
            // Re-evaluate with ast_available = true to trigger Governance Lock
            await betaLactamService.evaluateCase(inputContext, true);
        } catch (err) {
            // Expected to throw 403 GOVERNANCE LOCK
            setError(err.message);
            // We can auto-jump to Lab tab if they click this
            setCurrentStep(4);
        }
    };

    const handleLabComplete = () => {
        setCurrentStep(5);
    };

    const handlePostASTComplete = () => {
        // Reset for next patient
        setEncounterId(`ENC-${Math.random().toString(36).substr(2, 6).toUpperCase()}`);
        setInputContext(null);
        setEvalResult(null);
        setCurrentStep(1);
    };

    // ── Render Helpers ───────────────────────────────────────────────────────

    const renderCurrentScreen = () => {
        switch (currentStep) {
            case 1:
                return <CaseRegistration onComplete={handleRegistrationComplete} />;
            case 2:
                return (
                    <SpectrumDashboard
                        inputs={inputContext}
                        result={evalResult}
                        onNext={() => setCurrentStep(3)}
                    />
                );
            case 3:
                return (
                    <GenerationRecommendation
                        encounterId={encounterId}
                        inputContext={inputContext}
                        evalResult={evalResult}
                        recommendations={evalResult.recommendations}
                        topFeatures={evalResult.top_feature_influences}
                        onASTRestriction={handleASTRestriction}
                        onProceedLabel={() => setCurrentStep(4)}
                    />
                );
            case 4:
                return (
                    <LabEntryForm
                        encounterId={encounterId}
                        inputContext={inputContext}
                        resultContext={evalResult}
                        onComplete={handleLabComplete}
                    />
                );
            case 5:
                const topGen = evalResult?.top_generation_recommendation;
                return (
                    <PostASTReview
                        encounterId={encounterId}
                        empiricGeneration={topGen}
                        onComplete={handlePostASTComplete}
                    />
                );
            default:
                return <CaseRegistration onComplete={handleRegistrationComplete} />;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 p-6 md:p-10 font-sans">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Global Header */}
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">
                            Beta-Lactam Spectrum Predictor
                        </h1>
                        <p className="text-slate-500 dark:text-gray-400 font-medium mt-1">
                            Generation-level susceptibility forecasting and antimicrobial stewardship
                        </p>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={() => setShowAuditLogs(true)}
                            className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 text-slate-700 dark:text-gray-200 hover:bg-slate-50 dark:hover:bg-gray-700 hover:text-indigo-600 dark:hover:text-indigo-400 px-4 py-2 rounded-lg font-bold text-sm shadow-sm transition-colors flex items-center gap-2"
                        >
                            <Shield className="w-4 h-4" />
                            Governance Audit
                        </button>
                    </div>
                </div>

                {/* Global Error Alert */}
                {error && (
                    <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-xl flex gap-3 shadow-sm animate-in zoom-in-95">
                        <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                        <div>
                            <h4 className="text-sm font-bold text-red-800">System Alert</h4>
                            <p className="text-sm text-red-700 mt-1">{error}</p>
                        </div>
                    </div>
                )}

                {/* Stepper Navigation */}
                <div className="max-w-4xl mx-auto">
                    <nav aria-label="Progress">
                        <ol role="list" className="flex items-center">
                            {steps.map((step, stepIdx) => (
                                <li key={step.name} className={`relative ${stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : ''}`}>
                                    <div className="absolute inset-0 flex items-center" aria-hidden="true">
                                        <div className={`h-0.5 w-full ${step.id < currentStep ? 'bg-indigo-600' : 'bg-slate-200'}`} />
                                    </div>
                                    <button
                                        onClick={() => {
                                            // Allow navigating back to completed steps
                                            if (step.id < currentStep) setCurrentStep(step.id);
                                        }}
                                        disabled={step.id > currentStep}
                                        className={`relative flex h-10 w-10 items-center justify-center rounded-full transition-colors ${step.id < currentStep
                                            ? 'bg-indigo-600 hover:bg-indigo-700 cursor-pointer'
                                            : step.id === currentStep
                                                ? 'bg-white dark:bg-gray-900 border-2 border-indigo-600 dark:border-indigo-500'
                                                : 'bg-white dark:bg-gray-900 border-2 border-slate-300 dark:border-gray-700 cursor-not-allowed'
                                            }`}
                                    >
                                        <step.icon className={`h-5 w-5 ${step.id < currentStep
                                            ? 'text-white'
                                            : step.id === currentStep
                                                ? 'text-indigo-600'
                                                : 'text-slate-400'
                                            }`} />
                                    </button>
                                    <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-500 dark:text-gray-400 w-max">
                                        {step.name}
                                    </span>
                                </li>
                            ))}
                        </ol>
                    </nav>
                </div>

                <div className="pt-8">
                    {renderCurrentScreen()}
                </div>
            </div>

            {/* Modals */}
            {showAuditLogs && <AuditLogView onClose={() => setShowAuditLogs(false)} />}
        </div>
    );
};

export default BetaLactamModule;
