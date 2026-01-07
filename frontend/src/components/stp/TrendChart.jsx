
import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';

const TrendChart = ({ data, metric = "resistance_rate", title }) => {
    return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm h-72">
            <h4 className="text-sm font-bold text-slate-700 dark:text-gray-200 mb-4">{title}</h4>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis
                        dataKey="date"
                        stroke="#9CA3AF"
                        fontSize={10}
                        tickFormatter={(str) => new Date(str).toLocaleDateString()}
                    />
                    <YAxis stroke="#9CA3AF" fontSize={10} domain={[0, 1]} />
                    <Tooltip
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Rate']}
                        labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    />
                    <Area
                        type="monotone"
                        dataKey={metric}
                        stroke="#8884d8"
                        fillOpacity={1}
                        fill="url(#colorMetric)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TrendChart;
