import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

const Sparkline = ({ data }) => {
    // Data expected: array of numbers [60, 70, 65, 80]
    if (!data || data.length < 2) return <span className="text-xs text-gray-500">-</span>;

    const chartData = data.map((val, i) => ({ i, val }));
    const lastVal = data[data.length - 1];

    // Determine color based on last value
    const strokeColor = lastVal >= 80 ? '#22c55e' : (lastVal >= 60 ? '#eab308' : '#ef4444');
    const fillColor = lastVal >= 80 ? '#22c55e' : (lastVal >= 60 ? '#eab308' : '#ef4444');

    return (
        <div style={{ width: 60, height: 24 }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <YAxis domain={[0, 100]} hide />
                    <Area
                        type="monotone"
                        dataKey="val"
                        stroke={strokeColor}
                        fill={fillColor}
                        fillOpacity={0.2}
                        strokeWidth={2}
                        dot={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default Sparkline;
