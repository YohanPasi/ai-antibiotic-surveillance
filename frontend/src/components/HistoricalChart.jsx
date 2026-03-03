import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Activity } from 'lucide-react';

/* ── custom tooltip ─────────────────────────────────────────────────── */
const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="rounded-xl border border-white/10 bg-gray-950 shadow-2xl px-4 py-3 min-w-[160px]">
            <p className="text-xs font-bold text-gray-400 mb-2 border-b border-white/5 pb-1.5">{label}</p>
            {payload.map((p) => (
                <div key={p.name} className="flex items-center justify-between gap-4 py-0.5">
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
                        <span className="text-xs text-gray-400">{p.name}</span>
                    </div>
                    <span className="text-xs font-bold text-white tabular-nums">
                        {p.value != null ? `${Number(p.value).toFixed(1)}%` : '—'}
                    </span>
                </div>
            ))}
        </div>
    );
};

/* ── custom legend ──────────────────────────────────────────────────── */
const CustomLegend = ({ payload }) => (
    <div className="flex items-center gap-4 justify-end flex-wrap mb-2">
        {payload?.map(entry => (
            <div key={entry.value} className="flex items-center gap-1.5">
                <span className="w-6 h-0.5 inline-block rounded-full"
                    style={{
                        background: entry.color,
                        borderTop: entry.payload?.strokeDasharray ? `2px dashed ${entry.color}` : undefined,
                    }} />
                <span className="text-[11px] text-gray-500 font-medium">{entry.value}</span>
            </div>
        ))}
    </div>
);

/* ── main chart component ───────────────────────────────────────────── */
export default function HistoricalChart({ data, prediction, loading }) {

    if (loading) return (
        <div className="h-80 flex flex-col items-center justify-center gap-4
                        rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
                <div className="absolute inset-0 rounded-full border-t-2 border-blue-400 animate-spin" />
            </div>
            <p className="text-sm text-gray-500 animate-pulse">Loading chart…</p>
        </div>
    );

    if (!data || data.length === 0) return (
        <div className="h-80 flex flex-col items-center justify-center gap-3
                        rounded-xl border border-white/5 bg-white/[0.02] text-gray-600">
            <Activity className="w-10 h-10 opacity-20" />
            <p className="text-sm">No historical data available</p>
            <p className="text-xs text-gray-700">Select different parameters or collect more data</p>
        </div>
    );

    /* build chart data */
    const chartData = data.map(point => ({
        date: point.date
            || new Date(point.week_start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        'Observed S%': point.observed_s !== undefined ? point.observed_s : point.susceptibility_percent,
        'Baseline': point.expected_s,
    }));

    if (prediction) {
        const isNewFormat = prediction.predicted_s !== undefined;
        if (isNewFormat) {
            chartData.push({
                date: prediction.date || prediction.week,
                'Predicted S%': prediction.predicted_s,
                'Baseline': data[data.length - 1]?.expected_s,
            });
        } else if (data.length > 0) {
            const lastDate = new Date(data[data.length - 1].week_start_date);
            const nextWeek = new Date(lastDate);
            nextWeek.setDate(nextWeek.getDate() + 7);
            chartData.push({
                date: nextWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                'Predicted S%': prediction.prediction,
            });
        }
    }

    return (
        <div className="rounded-xl border border-white/5 bg-white/[0.02] px-5 pt-5 pb-4">
            {/* title row */}
            <div className="flex items-center justify-between mb-1">
                <div>
                    <h4 className="text-sm font-bold text-white">Susceptibility Trend</h4>
                    <p className="text-xs text-gray-500 mt-0.5">Observed vs. Baseline vs. Forecast</p>
                </div>
                {prediction?.predicted_s != null && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-violet-300
                                     bg-violet-500/10 border border-violet-500/20 px-3 py-1.5 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                        Forecast: {prediction.predicted_s}%
                    </span>
                )}
            </div>

            <ResponsiveContainer width="100%" height={320}>
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>

                    <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255,255,255,0.04)"
                        vertical={false}
                    />

                    <XAxis
                        dataKey="date"
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

                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.06)', strokeWidth: 1 }} />
                    <Legend content={<CustomLegend />} verticalAlign="top" />

                    {/* Critical breakpoint */}
                    <ReferenceLine
                        y={60}
                        stroke="#ef4444"
                        strokeWidth={1}
                        strokeDasharray="4 3"
                        strokeOpacity={0.4}
                        label={{
                            value: 'Critical 60%',
                            position: 'insideTopRight',
                            fill: '#ef4444',
                            fontSize: 10,
                            opacity: 0.6,
                        }}
                    />

                    {/* Baseline (dashed muted) */}
                    <Line
                        type="monotone"
                        dataKey="Baseline"
                        stroke="#4b5563"
                        strokeWidth={1.5}
                        strokeDasharray="5 4"
                        dot={false}
                        name="Statistical Baseline"
                        connectNulls
                    />

                    {/* Observed S% (primary solid) */}
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

                    {/* Forecast (hollow circle + dashed) */}
                    <Line
                        type="monotone"
                        dataKey="Predicted S%"
                        stroke="#a78bfa"
                        strokeWidth={2}
                        strokeDasharray="5 4"
                        dot={{ r: 6, fill: 'transparent', stroke: '#a78bfa', strokeWidth: 2.5 }}
                        activeDot={{ r: 8, fill: 'transparent', stroke: '#a78bfa', strokeWidth: 2 }}
                        name="LSTM Forecast"
                        connectNulls
                    />

                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
