import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

const Sparkline = ({ data }) => {
    if (!data || data.length < 2) return <span className="text-xs text-gray-600">—</span>;

    const chartData = data.map((val, i) => ({ i, val }));
    const lastVal = data[data.length - 1];

    const strokeColor = lastVal >= 80 ? '#34d399' : lastVal >= 60 ? '#fbbf24' : '#f87171';
    const fillColor = lastVal >= 80 ? '#34d399' : lastVal >= 60 ? '#fbbf24' : '#f87171';

    return (
        <div style={{ width: 56, height: 22 }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <YAxis domain={[0, 100]} hide />
                    <Area
                        type="monotone"
                        dataKey="val"
                        stroke={strokeColor}
                        fill={fillColor}
                        fillOpacity={0.15}
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default Sparkline;
