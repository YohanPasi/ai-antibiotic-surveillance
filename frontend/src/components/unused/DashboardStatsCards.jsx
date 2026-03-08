import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Activity } from 'lucide-react';

const DashboardStatsCards = () => {
    const [stats, setStats] = useState({
        totalSamples: 1247,
        resistantCases: 342,
        activeOutbreaks: 3,
        predictionAccuracy: 94.2
    });

    const [organizationStatistics, setOrganizationStatistics] = useState([
        { name: 'MRSA', count: 45, trend: 'up', change: 12 },
        { name: 'ESBL', count: 78, trend: 'down', change: 8 },
        { name: 'Pseudomonas', count: 34, trend: 'stable', change: 2 },
        { name: 'Acinetobacter', count: 23, trend: 'up', change: 15 }
    ]);

    const [wardData, setWardData] = useState([
        { ward: 'ICU', samples: 234, resistant: 89, rate: 38 },
        { ward: 'Medical', samples: 456, resistant: 123, rate: 27 },
        { ward: 'Surgical', samples: 345, resistant: 78, rate: 23 },
        { ward: 'Pediatric', samples: 212, resistant: 52, rate: 25 }
    ]);

    const [timeSeriesData, setTimeSeriesData] = useState([
        { month: 'Jan', MRSA: 12, ESBL: 25, NF: 8 },
        { month: 'Feb', MRSA: 15, ESBL: 22, NF: 10 },
        { month: 'Mar', MRSA: 18, ESBL: 28, NF: 12 },
        { month: 'Apr', MRSA: 14, ESBL: 24, NF: 9 },
        { month: 'May', MRSA: 20, ESBL: 30, NF: 15 },
        { month: 'Jun', MRSA: 22, ESBL: 32, NF: 14 }
    ]);

    const [resistanceDistribution, setResistanceDistribution] = useState([
        { name: 'Sensitive', value: 65, color: '#10b981' },
        { name: 'Intermediate', value: 15, color: '#f59e0b' },
        { name: 'Resistant', value: 20, color: '#ef4444' }
    ]);

    const [recentAlerts, setRecentAlerts] = useState([
        { id: 1, type: 'critical', message: 'MRSA outbreak detected in ICU', time: '10 min ago' },
        { id: 2, type: 'warning', message: 'Rising ESBL trend in Medical Ward', time: '1 hour ago' },
        { id: 3, type: 'info', message: 'Weekly report generated', time: '2 hours ago' }
    ]);

    const StatCard = ({ title, value, icon: Icon, trend, change, color }) => (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-800">
            <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
                {trend && (
                    <div className={`flex items-center gap-1 text-sm font-medium ${trend === 'up' ? 'text-red-500' : trend === 'down' ? 'text-green-500' : 'text-gray-500'
                        }`}>
                        {trend === 'up' ? <TrendingUp className="w-4 h-4" /> :
                            trend === 'down' ? <TrendingDown className="w-4 h-4" /> : null}
                        {change}%
                    </div>
                )}
            </div>
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
        </div>
    );

    const ChartCard = ({ title, children }) => (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-800">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">{title}</h3>
            {children}
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Samples"
                    value={stats.totalSamples.toLocaleString()}
                    icon={Activity}
                    color="bg-gradient-to-br from-blue-500 to-cyan-500"
                />
                <StatCard
                    title="Resistant Cases"
                    value={stats.resistantCases}
                    icon={AlertTriangle}
                    trend="up"
                    change={8}
                    color="bg-gradient-to-br from-red-500 to-rose-500"
                />
                <StatCard
                    title="Active Outbreaks"
                    value={stats.activeOutbreaks}
                    icon={TrendingUp}
                    trend="stable"
                    change={0}
                    color="bg-gradient-to-br from-amber-500 to-orange-500"
                />
                <StatCard
                    title="Prediction Accuracy"
                    value={`${stats.predictionAccuracy}%`}
                    icon={CheckCircle}
                    trend="up"
                    change={2.5}
                    color="bg-gradient-to-br from-emerald-500 to-teal-500"
                />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Time Series Chart */}
                <ChartCard title="Monthly Trends">
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeSeriesData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="month" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="MRSA" stroke="#ef4444" strokeWidth={2} />
                            <Line type="monotone" dataKey="ESBL" stroke="#3b82f6" strokeWidth={2} />
                            <Line type="monotone" dataKey="NF" stroke="#f59e0b" strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* Ward Distribution */}
                <ChartCard title="Ward Distribution">
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={wardData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="ward" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px'
                                }}
                            />
                            <Legend />
                            <Bar dataKey="samples" fill="#10b981" />
                            <Bar dataKey="resistant" fill="#ef4444" />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* Resistance Distribution */}
                <ChartCard title="Resistance Distribution">
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={resistanceDistribution}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {resistanceDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* Recent Alerts */}
                <ChartCard title="Recent Alerts">
                    <div className="space-y-3">
                        {recentAlerts.map((alert) => (
                            <div
                                key={alert.id}
                                className={`p-4 rounded-lg border-l-4 ${alert.type === 'critical' ? 'bg-red-50 dark:bg-red-900/20 border-red-500' :
                                        alert.type === 'warning' ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-500' :
                                            'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                                    }`}
                            >
                                <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                                    {alert.message}
                                </p>
                                <p className="text-xs text-gray-600 dark:text-gray-400">{alert.time}</p>
                            </div>
                        ))}
                    </div>
                </ChartCard>
            </div>

            {/* Organism Statistics Table */}
            <ChartCard title="Pathogen Statistics">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200 dark:border-gray-800">
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Organism</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Count</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Trend</th>
                                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            {organizationStatistics.map((org, index) => (
                                <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                                    <td className="py-3 px-4 text-sm text-gray-900 dark:text-white font-medium">{org.name}</td>
                                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{org.count}</td>
                                    <td className="py-3 px-4">
                                        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${org.trend === 'up' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                                org.trend === 'down' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                    'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                                            }`}>
                                            {org.trend === 'up' ? <TrendingUp className="w-3 h-3" /> :
                                                org.trend === 'down' ? <TrendingDown className="w-3 h-3" /> : null}
                                            {org.trend}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">{org.change}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </ChartCard>
        </div>
    );
};

export default DashboardStatsCards;
