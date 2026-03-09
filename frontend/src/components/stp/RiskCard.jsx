import React from 'react';
import { AlertTriangle, ShieldAlert, BellRing } from 'lucide-react';

const RISK_CONFIG = {
    high: { bg: 'bg-red-50 border-red-200', text: 'text-red-700', bar: 'bg-red-500', icon: <ShieldAlert className="w-4 h-4 text-red-600 animate-pulse" />, label: 'High Risk' },
    medium: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-700', bar: 'bg-amber-500', icon: <AlertTriangle className="w-4 h-4 text-amber-600" />, label: 'Moderate Risk' },
    low: { bg: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700', bar: 'bg-emerald-500', icon: <BellRing className="w-4 h-4 text-emerald-600" />, label: 'Low Risk' },
};

/**
 * RiskCard — clinician-friendly risk display.
 * Props: ward, organism, antibiotic, probability (0–1), riskLevel ('high'|'medium'|'low'),
 *        uncertainty (0–1), horizon (string), compact (bool)
 */
const RiskCard = ({ ward, organism, antibiotic, probability = 0, riskLevel = 'low', uncertainty, horizon, compact = false }) => {
    const cfg = RISK_CONFIG[riskLevel?.toLowerCase()] || RISK_CONFIG.low;
    const pct = Math.round((probability ?? 0) * 100);

    return (
        <div className={`rounded-xl border p-4 ${cfg.bg} transition-shadow hover:shadow-md`}>
            {/* Risk label + icon */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-1.5">
                    {cfg.icon}
                    <span className={`text-xs font-bold ${cfg.text}`}>{cfg.label}</span>
                </div>
                {horizon && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.text}`}>
                        Next 7 days
                    </span>
                )}
            </div>

            {!compact && (
                <>
                    <p className={`font-bold text-sm ${cfg.text} leading-snug`}>{organism}</p>
                    <p className={`text-xs ${cfg.text} opacity-80 mt-0.5`}>{antibiotic}{ward ? ` · ${ward}` : ''}</p>
                </>
            )}

            {/* Probability */}
            <div className="mt-3">
                <div className="flex items-end justify-between mb-1">
                    <span className="text-xs text-slate-500">Likelihood of resistance increase</span>
                    <span className={`text-xl font-black ${cfg.text}`}>{pct}%</span>
                </div>
                <div className="w-full bg-black/10 rounded-full h-2 overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`} style={{ width: `${pct}%` }} />
                </div>
            </div>

            {/* Uncertainty — shown only if available, in plain language */}
            {uncertainty != null && !isNaN(uncertainty) && (
                <p className="text-[10px] text-slate-400 mt-2">
                    Estimate range: ±{(uncertainty * 100).toFixed(0)}%
                </p>
            )}
        </div>
    );
};

export default RiskCard;
