import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle, TrendingDown, TrendingUp, Minus,
    ChevronDown, ChevronUp, Activity, Cpu, Shield,
    BarChart2, Zap, CheckCircle, XCircle,
} from 'lucide-react';

/* ─────────────────────────────────────────────────────────────────────
   CockpitPanels.jsx — Phase C
   Three read-only display panels that translate backend intelligence
   into clinical and operational language.

   Panels:
     B — G8 Plain-English Translation
     C — Drift & Volatility Diagnostics (collapsible, IT-level)
     D — Model Governance & Performance

   Props:
     driftAnalysis   full run_drift_analysis() dict from backend
     forecast        { ci_lower, ci_upper, ci_source, predicted_s }
     organism        string
     antibiotic      string
     ward            string

   Rules:
     • ZERO business logic.
     • Every string / number sourced from props.
     • Translation engine maps backend strings to clinical language.
─────────────────────────────────────────────────────────────────────── */

/* ═══════════════════════════════════════════════════════════════════
   PANEL B — G8 Plain-English Translation
═══════════════════════════════════════════════════════════════════ */

/* Maps backend primary_alert to clinical narrative */
const buildClinicalNarrative = ({ primary_alert, secondary_alerts = [],
    slope_detail, cusum_detail, organism, antibiotic, ward,
    observed_s, baseline_s, adaptive_tolerance }) => {

    // Safe accessors
    const obs = observed_s != null ? `${observed_s.toFixed(1)}%` : '—';
    const base = baseline_s != null ? `${baseline_s.toFixed(1)}%` : '—';
    const tol = adaptive_tolerance != null ? `${adaptive_tolerance.toFixed(1)}%` : '—';
    const slope = slope_detail?.slope_per_week != null
        ? `${Math.abs(slope_detail.slope_per_week).toFixed(1)}%/week` : null;
    const dir = slope_detail?.direction;

    switch (primary_alert) {

        case 'RED':
            return {
                severity: 'critical',
                headline: 'Susceptibility Breach — Immediate Review Required',
                body: `${antibiotic} susceptibility for ${organism} in Ward ${ward} has fallen to ${obs}, `
                    + `breaching the adaptive safety threshold (baseline ${base}, tolerance ±${tol}). `
                    + `This level of resistance erosion warrants immediate Antibiotic Stewardship Team review.`,
                action: 'Review empirical therapy protocols and escalate to clinical pharmacist.',
            };

        case 'DRIFT_WARNING':
            if (slope_detail?.slope_triggered) {
                return {
                    severity: 'warning',
                    headline: `Sustained ${dir === 'FALLING' ? 'Declining' : 'Rising'} Trend Detected`,
                    body: `Susceptibility is ${dir === 'FALLING' ? 'declining' : 'rising'} `
                        + `at ${slope || 'a sustained rate'} — faster than expected from historical noise. `
                        + `Current level: ${obs}, baseline expectation: ${base}. `
                        + `OLS regression slope has exceeded the adaptive noise threshold.`,
                    action: 'Monitor weekly. If decline continues for 2+ more weeks, escalate for stewardship review.',
                };
            }
            if (cusum_detail?.cusum_triggered) {
                return {
                    severity: 'warning',
                    headline: 'Sustained Regime Shift Detected (CUSUM)',
                    body: `The CUSUM control chart has detected a statistically significant, sustained `
                        + `shift in the ${antibiotic} resistance pattern for ${organism}. `
                        + `This is distinct from random week-to-week variation — it indicates a `
                        + `structural change in the resistance level (current: ${obs}, baseline: ${base}).`,
                    action: 'Investigate recent prescribing patterns, patient cohort changes, or formulary changes.',
                };
            }
            return {
                severity: 'warning',
                headline: 'Drift Signal Active',
                body: `A drift pattern has been detected in ${antibiotic} susceptibility for ${organism}. Current: ${obs}, baseline: ${base}.`,
                action: 'Review recent trend data and monitor closely.',
            };

        case 'DEGRADED':
            return {
                severity: 'degraded',
                headline: 'Forecasting Model Degraded',
                body: `The predictive model for ${antibiotic}/${organism} in Ward ${ward} has shown `
                    + `declining accuracy over the last 12 validated weeks. `
                    + `Current susceptibility (${obs}) is still within safe range, but forecast reliability is reduced. `
                    + `Auto-model selection will re-evaluate candidate models next cycle.`,
                action: 'No immediate clinical action needed. IT review of model performance recommended.',
            };

        case 'BIAS_WARNING':
            return {
                severity: 'bias',
                headline: 'Systematic Forecast Bias Detected',
                body: `The active model is systematically ${slope_detail?.direction === 'FALLING'
                    ? 'over-predicting' : 'under-predicting'} `
                    + `${antibiotic} susceptibility for ${organism}. `
                    + `This may indicate a structural shift the model has not yet adapted to. `
                    + `Current observed: ${obs}, model expected: ${base}.`,
                action: 'Consider triggering manual model re-evaluation. Bias exceeds 75% of MAE.',
            };

        case 'AMBER':
            return {
                severity: 'watch',
                headline: 'Susceptibility in Warning Band',
                body: `${antibiotic} susceptibility for ${organism} (Ward ${ward}) has entered the `
                    + `amber warning zone at ${obs}. Baseline is ${base} with adaptive tolerance ±${tol}. `
                    + `No breach yet, but the trend warrants increased monitoring frequency.`,
                action: 'Increase monitoring. No immediate escalation required unless the trend continues.',
            };

        case 'GREEN':
            return {
                severity: 'normal',
                headline: 'Stable — No Signals Detected',
                body: `${antibiotic} susceptibility for ${organism} (Ward ${ward}) is performing within `
                    + `expected parameters. Current: ${obs}, baseline: ${base}. `
                    + `CUSUM, slope, and volatility detectors show no active signals.`,
                action: null,
            };

        case 'INSUFFICIENT_DATA':
            return {
                severity: 'learning',
                headline: 'Learning Phase — Insufficient Validated Weeks',
                body: `This target has fewer than 6 weeks of validated forecast data. `
                    + `Advanced drift detection, adaptive confidence intervals, and alert hierarchy `
                    + `are disabled until sufficient data is gathered. `
                    + `Static ±10% confidence bands are shown as a safe placeholder.`,
                action: 'No action required. System is gathering baseline data automatically.',
            };

        default:
            return {
                severity: 'normal',
                headline: 'Monitoring Active',
                body: `${antibiotic}/${organism} in Ward ${ward} is under active surveillance.`,
                action: null,
            };
    }
};

const severityStyles = {
    critical: {
        banner: 'border-red-500/30 bg-red-500/8',
        icon: AlertTriangle, iconColor: 'text-red-400',
        headlineColor: 'text-red-400', dot: 'bg-red-500',
    },
    warning: {
        banner: 'border-orange-500/30 bg-orange-500/8',
        icon: TrendingDown, iconColor: 'text-orange-400',
        headlineColor: 'text-orange-400', dot: 'bg-orange-400',
    },
    degraded: {
        banner: 'border-rose-500/30 bg-rose-500/8',
        icon: Activity, iconColor: 'text-rose-400',
        headlineColor: 'text-rose-400', dot: 'bg-rose-400',
    },
    bias: {
        banner: 'border-yellow-500/30 bg-yellow-500/8',
        icon: BarChart2, iconColor: 'text-yellow-400',
        headlineColor: 'text-yellow-400', dot: 'bg-yellow-400',
    },
    watch: {
        banner: 'border-amber-500/30 bg-amber-500/8',
        icon: AlertTriangle, iconColor: 'text-amber-400',
        headlineColor: 'text-amber-400', dot: 'bg-amber-400',
    },
    normal: {
        banner: 'border-emerald-500/20 bg-emerald-500/5',
        icon: CheckCircle, iconColor: 'text-emerald-400',
        headlineColor: 'text-emerald-400', dot: 'bg-emerald-400',
    },
    learning: {
        banner: 'border-gray-600/30 bg-gray-700/10',
        icon: Cpu, iconColor: 'text-gray-500',
        headlineColor: 'text-gray-400', dot: 'bg-gray-500',
    },
};

const PanelB = ({ driftAnalysis, organism, antibiotic, ward }) => {
    const narrative = buildClinicalNarrative({
        ...driftAnalysis,
        organism, antibiotic, ward,
    });
    const sty = severityStyles[narrative.severity] ?? severityStyles.normal;
    const Icon = sty.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={`rounded-xl border p-4 ${sty.banner}`}
        >
            <div className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                    <Icon className={`w-4 h-4 ${sty.iconColor}`} strokeWidth={2} />
                </div>
                <div className="flex-1 min-w-0">
                    {/* Headline */}
                    <p className={`text-sm font-bold mb-1.5 ${sty.headlineColor}`}>
                        {narrative.headline}
                    </p>
                    {/* Body */}
                    <p className="text-[12px] text-gray-300 leading-relaxed">
                        {narrative.body}
                    </p>
                    {/* Action */}
                    {narrative.action && (
                        <div className="mt-2.5 flex items-start gap-1.5">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500 mt-0.5">
                                Action:
                            </span>
                            <span className="text-[11px] text-gray-400 italic">
                                {narrative.action}
                            </span>
                        </div>
                    )}
                    {/* Secondary alerts */}
                    {(driftAnalysis?.secondary_alerts ?? []).length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                            {driftAnalysis.secondary_alerts.map(sec => (
                                <span key={sec}
                                    className="text-[10px] font-semibold px-2 py-0.5 rounded-full
                                               bg-white/5 border border-white/10 text-gray-400">
                                    {sec.replace(/_/g, ' ')}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   PANEL C — Epidemiological Shift Analysis
═══════════════════════════════════════════════════════════════════ */
const DiagRow = ({ label, value, sub, highlight }) => (
    <div className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
        <div>
            <p className="text-[11px] text-gray-300 font-medium">{label}</p>
            {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
        </div>
        <span className={`text-[12px] font-bold tabular-nums ${highlight ?? 'text-gray-200'}`}>
            {value}
        </span>
    </div>
);

const StatusBadge = ({ value, trueLabel = 'Detected', falseLabel = 'Stable',
    trueColor = 'text-orange-400', falseColor = 'text-emerald-400' }) => (
    <span className={`text-[12px] font-bold ${value ? trueColor : falseColor}`}>
        {value ? trueLabel : falseLabel}
    </span>
);

const PanelC = ({ driftAnalysis }) => {
    const [open, setOpen] = useState(false);

    const cusum = driftAnalysis?.cusum_detail ?? {};
    const slope = driftAnalysis?.slope_detail ?? {};
    const volat = driftAnalysis?.volatility_detail ?? {};
    const bypass = driftAnalysis?.bypass_reason;

    return (
        <div className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
            {/* Collapsible header */}
            <button
                onClick={() => setOpen(v => !v)}
                className="w-full text-left px-4 py-3 hover:bg-white/[0.02] transition-colors duration-150"
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-orange-400" strokeWidth={2} />
                        <div>
                            <span className="text-xs font-bold text-gray-200 block">
                                Epidemiological Pattern Analysis
                            </span>
                            <span className="text-[10px] text-gray-500 block mt-0.5 font-normal">
                                Distinguishing true resistance outbreaks from random biological noise
                            </span>
                        </div>
                    </div>
                    {open
                        ? <ChevronUp className="w-5 h-5 text-gray-500 flex-shrink-0" />
                        : <ChevronDown className="w-5 h-5 text-gray-500 flex-shrink-0" />
                    }
                </div>
            </button>

            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 pt-2 grid grid-cols-1 md:grid-cols-3 gap-6 border-t border-white/5">

                            {/* Bypass notice if cold-start */}
                            {bypass && (
                                <div className="col-span-full text-[11px] text-gray-400 italic border border-white/5
                                                rounded-lg px-3 py-2 bg-white/[0.01]">
                                    <span className="text-indigo-400 font-medium tracking-wide not-italic mr-2">LEARNING PHASE:</span>
                                    Advanced outbreak detectors are bypassed until 6 weeks of baseline susceptibility data is collected.
                                </div>
                            )}

                            {/* CUSUM -> Structural Shift */}
                            <div>
                                <div className="mb-3">
                                    <p className="text-[11px] font-bold text-gray-200">Structural Resistance Shift</p>
                                    <p className="text-[10px] text-gray-500 mt-0.5">Detects sudden, permanent changes in resistance regimes (e.g., new dominant strain).</p>
                                </div>
                                <DiagRow label="Shift Status"
                                    value={<StatusBadge value={cusum.cusum_triggered ?? false} />} />
                                <DiagRow label="Evidence Accumulator"
                                    value={cusum.C_pos != null ? cusum.C_pos.toFixed(2) : '—'}
                                    sub="Statistical evidence score"
                                    highlight={cusum.cusum_triggered ? 'text-orange-400' : 'text-gray-400'} />
                                <DiagRow label="Diagnostic Threshold"
                                    value={cusum.h != null ? cusum.h.toFixed(2) : '—'}
                                    sub="Dynamic biological limit"
                                    highlight="text-gray-500" />
                            </div>

                            {/* OLS Slope -> Gradual Trend */}
                            <div>
                                <div className="mb-3">
                                    <p className="text-[11px] font-bold text-gray-200">Gradual Resistance Trend</p>
                                    <p className="text-[10px] text-gray-500 mt-0.5">Detects slow but sustained creeping resistance over multiple weeks.</p>
                                </div>
                                <DiagRow label="Trend Status"
                                    value={<StatusBadge value={slope.slope_triggered ?? false} trueColor="text-red-400" />} />
                                <DiagRow label="Rate of Change"
                                    value={slope.slope_per_week != null
                                        ? `${Math.abs(slope.slope_per_week).toFixed(2)}% / week` : '—'}
                                    sub={`Direction: ${slope.direction ?? 'None'}`}
                                    highlight={slope.slope_triggered
                                        ? (slope.direction === 'FALLING' ? 'text-red-400' : 'text-emerald-400')
                                        : 'text-gray-400'} />
                                <DiagRow label="Warning Limit"
                                    value={slope.slope_threshold != null
                                        ? `${slope.slope_threshold.toFixed(2)}% / week` : '—'}
                                    sub="Adaptive baseline threshold" />
                            </div>

                            {/* Volatility -> Clinical Instability */}
                            <div>
                                <div className="mb-3">
                                    <p className="text-[11px] font-bold text-gray-200">Clinical Instability Spike</p>
                                    <p className="text-[10px] text-gray-500 mt-0.5">Detects when a historically stable target suddenly becomes highly unpredictable.</p>
                                </div>
                                <DiagRow label="Stability Status"
                                    value={<StatusBadge value={volat.volatility_triggered ?? false}
                                        trueLabel="Unstable Spike" falseLabel="Stable"
                                        trueColor="text-yellow-400" />} />
                                <DiagRow label="Instability Severity"
                                    value={volat.ratio != null ? `${volat.ratio.toFixed(2)}× higher` : '—'}
                                    sub="vs. historical baseline volatility"
                                    highlight={(volat.ratio ?? 0) > 2.0 ? 'text-yellow-400' : 'text-gray-400'} />
                                <DiagRow label="Current Fluctuations"
                                    value={volat.recent_std != null ? `±${volat.recent_std.toFixed(1)}%` : '—'}
                                    sub="Recent standard deviation" />
                            </div>

                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════
   PANEL D — AI Trust & Reliability
═══════════════════════════════════════════════════════════════════ */
const PanelD = ({ driftAnalysis, modelPerformance, forecast }) => {
    const mp = modelPerformance ?? {};
    const degraded = mp.degradation_flagged ?? driftAnalysis?.degradation_flagged ?? false;
    const activeModel = mp.active_model ?? driftAnalysis?.active_model_name ?? null;
    const rollingMae = mp.rolling_mae ?? driftAnalysis?.rolling_mae ?? null;
    const meanBias = mp.mean_bias ?? driftAnalysis?.mean_bias ?? null;
    const validatedCt = mp.validated_count ?? driftAnalysis?.validated_count ?? null;
    const ciSource = mp.ci_source ?? forecast?.ci_source ?? null;
    const ciHalf = mp.ci_half_width ?? forecast?.ci_half_width ?? null;

    // Status
    const perfStatus = (() => {
        if (validatedCt != null && validatedCt < 6) return 'GATHERING DATA';
        if (degraded) return 'RE-TRAINING NEEDED';
        if (rollingMae != null && rollingMae < 5) return 'HIGH RELIABILITY';
        if (rollingMae != null && rollingMae < 10) return 'GOOD RELIABILITY';
        return 'STANDARD MONITORING';
    })();

    const perfStyle = {
        'GATHERING DATA': { color: 'text-gray-400', bg: 'bg-gray-500/10 border-gray-500/20' },
        'RE-TRAINING NEEDED': { color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
        'HIGH RELIABILITY': { color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
        'GOOD RELIABILITY': { color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
        'STANDARD MONITORING': { color: 'text-gray-400', bg: 'bg-gray-500/10 border-gray-500/20' },
    }[perfStatus];

    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: 0.05 }}
            className="rounded-xl border border-white/5 bg-white/[0.02] p-4"
        >
            <div className="flex items-start justify-between mb-4 flex-wrap gap-2">
                <div className="flex items-start gap-3">
                    <Shield className="w-5 h-5 text-indigo-400 mt-0.5" strokeWidth={1.5} />
                    <div>
                        <span className="text-xs font-bold text-gray-200 block">AI Reliability & Trust Metrics</span>
                        <span className="text-[10px] text-gray-500 block mt-0.5 max-w-[400px]">
                            The surveillance engine continuously trains multiple predictive models in the background,
                            automatically promoting the most clinically accurate algorithm for each specific ward and organism.
                        </span>
                    </div>
                </div>
                <span className={`text-[10px] font-bold px-2 py-1 rounded-md border tracking-wide ${perfStyle.bg} ${perfStyle.color}`}>
                    {perfStatus}
                </span>
            </div>

            {/* Degradation warning */}
            {degraded && (
                <div className="mb-4 flex gap-2 p-3 rounded-lg border border-rose-500/20 bg-rose-500/5 items-start">
                    <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="text-[11px] font-bold text-rose-300">Predictive Accuracy Deteriorating</p>
                        <p className="text-[10px] text-rose-400/80 mt-0.5">
                            Recent biological shifts have made the current AI model less accurate. The system will
                            evaluate challenger models and auto-swap to a better algorithm on the next weekly cycle.
                        </p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-black/20 rounded-lg p-3 border border-white/5">
                <GovStat
                    label="Active Algorithm"
                    value={activeModel ?? 'Learning Phase'}
                    sub="Current champion model"
                />
                <GovStat
                    label="Historical Accuracy"
                    value={rollingMae != null ? `±${rollingMae.toFixed(1)}% Error` : '—'}
                    sub="Average miss over 12 weeks"
                    highlight={rollingMae != null
                        ? (rollingMae < 5 ? 'text-emerald-400' : rollingMae < 10 ? 'text-amber-400' : 'text-red-400')
                        : undefined}
                />
                <GovStat
                    label="Systematic Skew"
                    value={meanBias != null ? `${meanBias > 0 ? '+' : ''}${meanBias.toFixed(1)}%` : '—'}
                    sub={meanBias != null ? (meanBias > 0 ? "Tendency to over-predict" : "Tendency to under-predict") : "No significant bias"}
                    highlight={meanBias != null && Math.abs(meanBias) > 3 ? 'text-yellow-400' : undefined}
                />
                <GovStat
                    label="Learning Maturity"
                    value={validatedCt != null ? `${validatedCt} Weeks` : '—'}
                    sub="AI validation history"
                    highlight={validatedCt != null && validatedCt < 6 ? 'text-gray-500' : 'text-emerald-500/80'}
                />
            </div>

            {/* CI source note */}
            <div className="mt-3 flex items-center gap-2">
                <span className="text-[10px] text-gray-600 font-medium">Prediction Confidence Shadow:</span>
                <span className={`text-[10px] font-bold ${ciSource === 'adaptive' ? 'text-indigo-400' : 'text-gray-500'}`}>
                    {ciSource === 'adaptive'
                        ? `Adaptive shadow narrows/widens based on the active model's historical accuracy (Current: ±${ciHalf?.toFixed(1) ?? '?'}%)`
                        : `Standard ±10% shadow applied until sufficient data is gathered (Cold-start protocol)`}
                </span>
            </div>
        </motion.div>
    );
};

const GovStat = ({ label, value, sub, highlight }) => (
    <div className="flex flex-col gap-0.5">
        <p className={`text-sm font-bold tabular-nums ${highlight ?? 'text-gray-200'}`}>{value}</p>
        <p className="text-[10px] font-semibold text-gray-500">{label}</p>
        {sub && <p className="text-[10px] text-gray-700 italic">{sub}</p>}
    </div>
);

/* ═══════════════════════════════════════════════════════════════════
   EXPORT — Combined cockpit panels (B + C + D)
═══════════════════════════════════════════════════════════════════ */
export default function CockpitPanels({ driftAnalysis, modelPerformance, forecast, organism, antibiotic, ward }) {
    const da = driftAnalysis ?? {};
    const mp = modelPerformance ?? {};

    return (
        <div className="space-y-3">
            <PanelB
                driftAnalysis={da}
                organism={organism ?? '—'}
                antibiotic={antibiotic ?? '—'}
                ward={ward ?? '—'}
            />
            <PanelC driftAnalysis={da} />
            <PanelD driftAnalysis={da} modelPerformance={mp} forecast={forecast} />
        </div>
    );
}
