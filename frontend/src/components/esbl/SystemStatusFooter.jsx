
import React from 'react';

export const SystemStatusFooter = ({ versions, astLocked, onSimulateAST }) => {
    if (!versions) return null;

    return (
        <div className="fixed bottom-0 w-full bg-slate-900 text-slate-400 text-xs py-2 px-6 border-t border-slate-800 flex justify-between items-center z-50">
            <div className="flex gap-6 font-mono">
                <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    System Online
                </span>
                <span>
                    Model Ver: <span className="text-slate-200">{versions.model_version}</span>
                </span>
                <span>
                    Thresholds: <span className="text-slate-200">{versions.threshold_version}</span>
                </span>
                <span>
                    Gov Mode: {astLocked ? <span className="text-red-400 font-bold">POST-AST (LOCKED)</span> : <span className="text-blue-400">EMPIRIC (ACTIVE)</span>}
                </span>
            </div>

            <div>
                {!astLocked && (
                    <button
                        onClick={onSimulateAST}
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1 rounded border border-slate-700 text-xs transition-colors"
                    >
                        🛠️ Simulator: Upload AST Result
                    </button>
                )}
            </div>
        </div>
    );
};
