import React, { useState } from 'react';
import {
    ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine, ReferenceArea,
} from 'recharts';
import { Activity, AlertTriangle } from 'lucide-react';

/* ─────────────────────────────────────────────────────────────────────
   ProcessControlChart.jsx — Phase B (v2 — audit hardened)
   Epidemiological Process Control Chart

   Props:
     history           [{ week_start_date, observed_s, expected_s, date }]
     forecast          { predicted_s, ci_lower, ci_upper, ci_source,
                         predicted_week_start, date }
     driftAnalysis     run_drift_analysis() response from backend:
                         { primary_alert, adaptive_tolerance,
                           cusum_detail.cusum_triggered,
                           slope_detail.slope_triggered }
     modelSwitchEvents [{ target_week_start|week_start_date, new_model, old_model }]
     loading           bool

   Audit checks addressed (v2):
     ✅ Check 1 — All zone values clamped: Math.max(0, x)
     ✅ Check 2 — Zones only BELOW baseline, never above
     ✅ Check 3 — CI ReferenceArea keyed to forecast label only
     ✅ Check 4 — Drift dot only on last history point, NOT forecast
     ✅ Check 5 — Model switch uses target_week_start first
     ✅ Check 6 — History sliced to last 16 points defensively in component
     ✅ Amber zone uses correct Area stacking with [amberBottom, amberTop] tuple

   Rules:
     • Zero business logic. Everything comes from backend.
     • driftAnalysis.adaptive_tolerance is the authoritative tolerance.
     • ci_source = 'adaptive' → violet band; 'static_fallback' → grey band
─────────────────────────────────────────────────────────────────────── */

/* ── Custom Tooltip ─────────────────────────────────────────────── */
const PCC_Tooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const visible = payload.filter(p =>
        p.value != null && !['__amberBand__'].includes(p.name)
    );
    return (
        <div className="rounded-xl border border-white/10 bg-gray-950/95 shadow-2xl px-4 py-3 min-w-[180px]">
            <p className="text-[11px] font-bold text-gray-400 mb-2 border-b border-white/5 pb-1.5">{label}</p>
            {visible.map(p => (
                <div key={p.name} className="flex items-center justify-between gap-4 py-0.5">
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full"
                            style={{ background: p.color || p.fill || '#888' }} />
                        <span className="text-[11px] text-gray-400">{p.name}</span>
                    </div>
                    <span className="text-[11px] font-bold text-white tabular-nums">
                        {typeof p.value === 'number' ? `${p.value.toFixed(1)}%` : String(p.value)}
                    </span>
                </div>
            ))}
        </div>
    );
};

/* ── Custom Legend — excludes internal area series ────────────────── */
const PCC_Legend = ({ payload, isColdStart }) => (
    <div className="flex items-center gap-4 justify-end flex-wrap mb-2">
        {payload?.filter(e => !e.value?.startsWith('__'))
            .map(entry => (
                <div key={entry.value} className="flex items-center gap-1.5">
                    <span className="w-5 h-0.5 inline-block rounded-full"
                        style={{ background: entry.color }} />
                    <span className="text-[10px] text-gray-500 font-medium">{entry.value}</span>
                </div>
            ))}
        {isColdStart && (
            <span className="text-[10px] text-gray-600 italic ml-2">(cold-start · static ±10% CI)</span>
        )}
    </div>
);

/* ── Drift event dot (orange ring on last observed point) ─────────── */
const DriftDot = ({ cx, cy }) => (
    <g>
        <circle cx={cx} cy={cy} r={9} fill="#f97316" fillOpacity={0.15}
            stroke="#f97316" strokeWidth={1.5} />
        <circle cx={cx} cy={cy} r={4} fill="#f97316" />
    </g>
);

/* ── Main Component ─────────────────────────────────────────────── */
export default function ProcessControlChart({
    history = [],
    forecast = null,
    driftAnalysis = {},
    modelSwitchEvents = [],
    loading = false,
}) {
    const [showBands, setShowBands] = useState(true);

    /* ── guards ── */
    if (loading) return (
        <div className="h-96 flex flex-col items-center justify-center gap-4
                        rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
                <div className="absolute inset-0 rounded-full border-t-2 border-blue-400 animate-spin" />
            </div>
            <p className="text-sm text-gray-500 animate-pulse">Building process control chart…</p>
        </div>
    );
    if (!history?.length) return (
        <div className="h-96 flex flex-col items-center justify-center gap-3
                        rounded-xl border border-white/5 bg-white/[0.02] text-gray-600">
            <Activity className="w-10 h-10 opacity-20" />
            <p className="text-sm">No historical data available</p>
        </div>
    );

    /* ── Check 6: defensive 16-week slice (backend already does this,
         but chart doesn't need to render multi-year data) ── */
    const slicedHistory = history.slice(-16);

    /* ── Derive config from backend ── */
    const adaptiveTol = driftAnalysis?.adaptive_tolerance ?? 10.0;
    const isColdStart = driftAnalysis?.primary_alert === 'INSUFFICIENT_DATA'
        || forecast?.ci_source === 'static_fallback';
    const cusumTriggered = driftAnalysis?.cusum_detail?.cusum_triggered === true;
    const slopeTriggered = driftAnalysis?.slope_detail?.slope_triggered === true;
    const driftActive = cusumTriggered || slopeTriggered;

    /* ── Check 4: drift dot index (index in slicedHistory, not chartData) ── */
    const driftDotIdx = slicedHistory.length - 1;   // last OBSERVED point only

    /* ── Build chart series ── */
    const chartData = slicedHistory.map((pt, i) => {
        const baseline = pt.expected_s;
        // Check 1 + 2: zones clamped to [0, baseline-ε], never above baseline
        const redLine = baseline != null ? Math.max(0, +(baseline - adaptiveTol).toFixed(1)) : null;
        const amberLine = baseline != null ? Math.max(0, +(baseline - 2 * adaptiveTol).toFixed(1)) : null;
        return {
            label: pt.date || pt.week_start_date?.slice(5, 10),
            'Observed S%': pt.observed_s,
            Baseline: baseline,
            // Amber band encoded as [amberLine, redLine] for Area stacking
            // Check 2: only rendered below baseline
            ...((!isColdStart && baseline != null && redLine !== null && amberLine !== null) ? {
                amberBand: [amberLine, redLine],   // Recharts Area with values tuple
            } : {}),
            _isDriftPoint: i === driftDotIdx,      // Check 4
        };
    });

    /* ── Check 3: forecast label captured for CI ReferenceArea x1/x2 ── */
    let forecastLabel = null;
    if (forecast?.predicted_s != null) {
        forecastLabel = forecast.date || forecast.predicted_week_start?.slice(5, 10) || 'Forecast';
        const lastBaseline = slicedHistory.at(-1)?.expected_s;
        chartData.push({
            label: forecastLabel,
            Forecast: forecast.predicted_s,
            Baseline: lastBaseline,
            // No drift dot on forecast point (Check 4)
            _isDriftPoint: false,
        });
    }

    /* ── Static threshold lines from LAST baseline in history ── */
    const lastBaseline = slicedHistory.at(-1)?.expected_s;
    const redBreachLine = lastBaseline != null ? Math.max(0, +(lastBaseline - adaptiveTol).toFixed(1)) : null;
    const amberWarnLine = lastBaseline != null ? Math.max(0, +(lastBaseline - 2 * adaptiveTol).toFixed(1)) : null;

    /* ── Check 5: model switch events — prefer target_week_start ── */
    const switchLines = modelSwitchEvents
        .filter(e => e?.target_week_start || e?.week_start_date)
        .map(e => ({
            ...e,
            xKey: e.target_week_start?.slice(5, 10)
                || e.week_start_date?.slice(5, 10),
        }));

    return (
        <div className="rounded-xl border border-white/5 bg-white/[0.02] px-5 pt-5 pb-4 space-y-3">

            {/* ── Header ── */}
            <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                    <h4 className="text-sm font-bold text-white">
                        Epidemiological Process Control Chart
                    </h4>
                    <p className="text-[11px] text-gray-500 mt-0.5">
                        Adaptive tolerance ±{adaptiveTol.toFixed(1)}%
                        {isColdStart
                            ? <span className="text-gray-600 italic ml-1"> · cold-start (static bands)</span>
                            : <span className="text-gray-600 ml-1"> · Phase 4C</span>}
                    </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    {forecast?.ci_source && (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${forecast.ci_source === 'adaptive'
                            ? 'bg-violet-500/10 border-violet-500/20 text-violet-400'
                            : 'bg-gray-700/20 border-gray-600/20 text-gray-500'
                            }`}>
                            {forecast.ci_source === 'adaptive' ? 'Adaptive CI' : 'Static CI'}
                        </span>
                    )}
                    {driftActive && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1
                                         bg-orange-500/10 border border-orange-500/20 text-orange-400">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            Drift Detected
                        </span>
                    )}
                    {!isColdStart && (
                        <button
                            onClick={() => setShowBands(v => !v)}
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border transition-colors ${showBands
                                ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                                : 'bg-white/5 border-white/10 text-gray-500'
                                }`}
                        >
                            {showBands ? 'Hide Bands' : 'Show Bands'}
                        </button>
                    )}
                </div>
            </div>

            {/* ── Chart ── */}
            <ResponsiveContainer width="100%" height={340}>
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.04)"
                        vertical={false}
                    />
                    <XAxis
                        dataKey="label"
                        stroke="rgba(255,255,255,0.08)"
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        tickLine={false}
                        axisLine={{ stroke: 'rgba(255,255,255,0.06)' }}
                    />
                    <YAxis
                        stroke="rgba(255,255,255,0.08)"
                        domain={[0, 100]}
                        tick={{ fill: '#6b7280', fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={v => `${v}%`}
                        width={38}
                    />

                    <Tooltip
                        content={<PCC_Tooltip />}
                        cursor={{ stroke: 'rgba(255,255,255,0.06)', strokeWidth: 1 }}
                    />
                    <Legend
                        content={<PCC_Legend isColdStart={isColdStart} />}
                        verticalAlign="top"
                    />

                    {/* ── Amber warning band — only below baseline ── */}
                    {!isColdStart && showBands && (
                        <Area
                            type="monotone"
                            dataKey="amberBand"
                            stroke="none"
                            fill="#f59e0b"
                            fillOpacity={0.10}
                            name="__amberBand__"
                            legendType="none"
                            activeDot={false}
                            connectNulls
                            isAnimationActive={false}
                        />
                    )}

                    {/* ── Red breach threshold ── */}
                    {!isColdStart && showBands && redBreachLine != null && (
                        <ReferenceLine
                            y={redBreachLine}
                            stroke="#ef4444" strokeWidth={1.5}
                            strokeDasharray="5 3" strokeOpacity={0.65}
                            label={{
                                value: `Breach ${redBreachLine}%`,
                                position: 'insideTopRight',
                                fill: '#ef4444', fontSize: 9, opacity: 0.7,
                            }}
                        />
                    )}

                    {/* ── Amber watch threshold ── */}
                    {!isColdStart && showBands && amberWarnLine != null && (
                        <ReferenceLine
                            y={amberWarnLine}
                            stroke="#f59e0b" strokeWidth={1}
                            strokeDasharray="3 4" strokeOpacity={0.4}
                            label={{
                                value: `Watch ${amberWarnLine}%`,
                                position: 'insideTopRight',
                                fill: '#f59e0b', fontSize: 9, opacity: 0.55,
                            }}
                        />
                    )}

                    {/* ── Model switch vertical lines (Check 5: target_week_start) ── */}
                    {switchLines.map((sw, i) => (
                        <ReferenceLine key={i} x={sw.xKey}
                            stroke="#a78bfa" strokeWidth={1}
                            strokeDasharray="4 3" strokeOpacity={0.5}
                            label={{
                                value: `→ ${sw.new_model ?? 'Model switch'}`,
                                position: 'top', fill: '#a78bfa', fontSize: 9, opacity: 0.7,
                            }}
                        />
                    ))}

                    {/* ── CI forecast band (Check 3: x1=x2=forecastLabel only) ── */}
                    {forecast?.ci_lower != null && forecast?.ci_upper != null && forecastLabel != null && (
                        <ReferenceArea
                            x1={forecastLabel} x2={forecastLabel}
                            y1={Math.max(0, forecast.ci_lower)}
                            y2={Math.min(100, forecast.ci_upper)}
                            fill={isColdStart ? '#6b7280' : '#a78bfa'}
                            fillOpacity={0.18}
                            stroke={isColdStart ? '#6b7280' : '#a78bfa'}
                            strokeOpacity={0.35}
                            strokeWidth={1}
                        />
                    )}

                    {/* ── Baseline (dashed muted) ── */}
                    <Line
                        type="monotone"
                        dataKey="Baseline"
                        stroke="#4b5563"
                        strokeWidth={1.5}
                        strokeDasharray="5 4"
                        dot={false}
                        name="Baseline"
                        connectNulls
                    />

                    {/* ── Observed S% (primary solid line) ── */}
                    <Line
                        type="monotone"
                        dataKey="Observed S%"
                        stroke="#60a5fa"
                        strokeWidth={2.5}
                        dot={{ r: 3.5, fill: '#60a5fa', stroke: '#1e3a5f', strokeWidth: 2 }}
                        activeDot={{ r: 6, fill: '#60a5fa', stroke: '#1e40af', strokeWidth: 2 }}
                        name="Observed S%"
                        connectNulls
                    />

                    {/* ── Drift event overlay — separate Line with same dataKey renders
                         an orange ring ONLY on the last observed point via a custom dot
                         that checks _isDriftPoint flag ── */}
                    {driftActive && (
                        <Line
                            type="monotone"
                            dataKey="Observed S%"
                            stroke="none"
                            dot={(props) => {
                                if (!props.payload?._isDriftPoint) return null;
                                return (
                                    <g key={`drift-${props.index}`}>
                                        <circle cx={props.cx} cy={props.cy} r={10}
                                            fill="#f97316" fillOpacity={0.15}
                                            stroke="#f97316" strokeWidth={1.5} />
                                        <circle cx={props.cx} cy={props.cy} r={4}
                                            fill="#f97316" />
                                    </g>
                                );
                            }}
                            activeDot={false}
                            legendType="none"
                            name="__driftOverlay__"
                            connectNulls
                            isAnimationActive={false}
                        />
                    )}

                    {/* ── Forecast point (hollow violet circle) ── */}
                    <Line
                        type="monotone"
                        dataKey="Forecast"
                        stroke="#a78bfa"
                        strokeWidth={2}
                        strokeDasharray="5 4"
                        dot={{ r: 6, fill: 'transparent', stroke: '#a78bfa', strokeWidth: 2.5 }}
                        activeDot={{ r: 8, fill: 'transparent', stroke: '#a78bfa', strokeWidth: 2 }}
                        name="AI Forecast"
                        connectNulls
                    />

                </ComposedChart>
            </ResponsiveContainer>

            {/* ── Band legend / explanation ── */}
            {!isColdStart && showBands && (
                <div className="flex items-center gap-5 flex-wrap pt-2 border-t border-white/[0.04]">
                    <div className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-sm bg-amber-400/15 border border-amber-400/30" />
                        <span className="text-[10px] text-gray-500">
                            Amber [{amberWarnLine}% – {redBreachLine}%]
                        </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="w-4 h-px bg-red-400/60" style={{ display: 'inline-block' }} />
                        <span className="text-[10px] text-gray-500">
                            Red breach below {redBreachLine}%
                        </span>
                    </div>
                    {driftActive && (
                        <div className="flex items-center gap-1.5">
                            <span className="w-3 h-3 rounded-full bg-orange-400/30 border border-orange-400" />
                            <span className="text-[10px] text-gray-500">
                                {cusumTriggered ? 'CUSUM' : 'Slope'} drift marker
                            </span>
                        </div>
                    )}
                    <span className="ml-auto text-[10px] text-gray-600">
                        ±{adaptiveTol.toFixed(1)}% adaptive tol · Phase 4C
                    </span>
                </div>
            )}
        </div>
    );
}
