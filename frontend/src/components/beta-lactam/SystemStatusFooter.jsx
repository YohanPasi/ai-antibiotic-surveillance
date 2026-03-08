import React from 'react';
import { Database, Shield, Zap, Info } from 'lucide-react';

const SystemStatusFooter = ({ evalResult }) => {
    // metadata: { model_version, evidence_version, features_used }
    const metadata = evalResult?.metadata;
    const isLive = !!evalResult;

    return (
        <div className="max-w-4xl mx-auto mt-8 flex flex-wrap items-center justify-between gap-4 text-xs font-medium text-slate-500 bg-white/50 border border-slate-200/50 rounded-xl px-4 py-3 backdrop-blur-sm animate-in fade-in duration-700">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isLive ? 'bg-emerald-400' : 'bg-slate-400'}`}></span>
                        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isLive ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
                    </span>
                    {isLive ? 'Live Beta-Lactam Engine' : 'System Standby'}
                </div>

                <div className="flex items-center gap-1.5 border-l border-slate-200 pl-6">
                    <Database className="w-3.5 h-3.5 text-slate-400" />
                    Artifact Version: <span className="text-slate-700">{metadata?.evidence_version || 'v1.0'}</span>
                </div>

                <div className="flex items-center gap-1.5 border-l border-slate-200 pl-6">
                    <Zap className="w-3.5 h-3.5 text-slate-400" />
                    Active Features: <span className="text-slate-700">{metadata?.features_used || 0}</span>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-indigo-400" />
                    Governance: <span className="text-slate-700">Enforced</span>
                </div>

                <div className="flex items-center gap-1.5 border-l border-slate-200 pl-4">
                    <Info className="w-3.5 h-3.5 text-slate-400" />
                    Model Build: <span className="text-slate-700 font-mono text-[10px]">{metadata?.model_version || 'unknown'}</span>
                </div>
            </div>
        </div>
    );
};

export default SystemStatusFooter;
