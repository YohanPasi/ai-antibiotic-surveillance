import React from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    const value = payload[0]?.value;
    const pct = value != null ? (value * 100).toFixed(1) : '—';
    const isHigh = value > 0.5;
    const isMed = value > 0.2;

    return (
        <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl shadow-lg px-4 py-3">
            <p className="text-xs text-slate-500 mb-1">{new Date(label).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
            <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isHigh ? 'bg-red-500' : isMed ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                <span className="text-sm font-bold text-slate-800 dark:text-white">{pct}% Resistance</span>
            </div>
        </div>
    );
};

/**
 * TrendChart — displays weekly resistance rate as a gradient area chart.
 * data: [{ date: string, resistance_rate: number (0–1) }]
 */
const TrendChart = ({ data = [], metric = 'resistance_rate', title }) => {
    if (!data || data.length === 0) {
        return (
            <div className="h-56 flex items-center justify-center bg-gray-50 dark:bg-gray-700 rounded-xl border border-dashed border-gray-200 dark:border-gray-600">
                <p className="text-sm text-slate-400">No trend data available</p>
            </div>
        );
    }

    return (
        <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <defs>
                        <linearGradient id="stpGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#a855f7" stopOpacity={0.25} />
                            <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                    <XAxis
                        dataKey="date"
                        stroke="#9CA3AF"
                        fontSize={10}
                        tickFormatter={str => {
                            try { return new Date(str).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }); }
                            catch { return str; }
                        }}
                        tickLine={false}
                        tickCount={8}
                    />
                    <YAxis
                        stroke="#9CA3AF"
                        fontSize={10}
                        domain={[0, 1]}
                        tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    {/* Reference lines for clinical risk thresholds */}
                    <ReferenceLine y={0.5} stroke="#EF4444" strokeDasharray="4 3" label={{ value: 'High threshold', position: 'insideTopRight', fontSize: 9, fill: '#EF4444' }} />
                    <ReferenceLine y={0.2} stroke="#F59E0B" strokeDasharray="4 3" label={{ value: 'Watch threshold', position: 'insideTopRight', fontSize: 9, fill: '#F59E0B' }} />
                    <Area
                        type="monotone"
                        dataKey={metric}
                        stroke="#a855f7"
                        strokeWidth={2.5}
                        fillOpacity={1}
                        fill="url(#stpGrad)"
                        dot={false}
                        activeDot={{ r: 5, fill: '#a855f7', stroke: '#fff', strokeWidth: 2 }}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TrendChart;
