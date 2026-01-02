import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Area } from 'recharts'

export default function HistoricalChart({ data, prediction, loading }) {
    if (loading) {
        return (
            <div className="card h-96 flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
                    <p className="text-gray-400">Loading chart...</p>
                </div>
            </div>
        )
    }

    if (!data || data.length === 0) {
        return (
            <div className="card h-96 flex items-center justify-center">
                <div className="text-center text-gray-400">
                    <div className="text-5xl mb-4">📊</div>
                    <p>No historical data available</p>
                    <p className="text-sm mt-2">Select different parameters or collect more data</p>
                </div>
            </div>
        )
    }

    // Prepare chart data
    const chartData = data.map((point) => ({
        date: point.date || new Date(point.week_start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        'S%': point.observed_s !== undefined ? point.observed_s : point.susceptibility_percent,
        // Fallback for different data structures
        'Baseline': point.expected_s // Mapped from new endpoint
    }))

    // Add forecast point if available (New Structure)
    if (prediction) {
        // Check if prediction is correct format from new endpoint
        const isNewFormat = prediction.predicted_s !== undefined;

        if (isNewFormat) {
            chartData.push({
                date: prediction.date || prediction.week,
                'Predicted S%': prediction.predicted_s,
                'Baseline': data[data.length - 1]?.expected_s // Extend baseline visually? or leave null
            })
        } else if (data.length > 0) {
            // Legacy format support
            const lastDate = new Date(data[data.length - 1].week_start_date)
            const nextWeek = new Date(lastDate)
            nextWeek.setDate(nextWeek.getDate() + 7)

            chartData.push({
                date: nextWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                'Predicted S%': prediction.prediction,
                'Lower Bound': prediction.lower_bound,
                'Upper Bound': prediction.upper_bound
            })
        }
    }

    return (
        <div className="card bg-gray-900 border border-gray-700 p-4 rounded-lg">
            <h2 className="text-xl font-bold text-gray-200 mb-2 flex items-center">
                📈 Susceptibility Trend Analysis
            </h2>
            <p className="text-xs text-gray-400 mb-6">Visualizing Observed vs. Baseline vs. Forecast</p>

            <ResponsiveContainer width="100%" height={350}>
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                    <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                    <YAxis stroke="#94a3b8" domain={[0, 100]} label={{ value: 'Susceptibility %', angle: -90, position: 'insideLeft', style: { fill: '#64748b' } }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                    <Legend verticalAlign="top" height={36} />

                    {/* Zones */}
                    <ReferenceLine y={60} label="Critical Breakpoint" stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />

                    {/* Statistical Baseline (Muted Line) */}
                    <Line type="monotone" dataKey="Baseline" stroke="#64748b" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Statistical Baseline" />

                    {/* Observed S% (Solid Line) */}
                    <Line type="monotone" dataKey="S%" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, fill: '#3b82f6' }} activeDot={{ r: 6 }} name="Observed S%" />

                    {/* Forecast (Hollow Circle + Dotted) */}
                    <Line type="monotone" dataKey="Predicted S%" stroke="#a855f7" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 6, fill: 'transparent', stroke: '#a855f7', strokeWidth: 2 }} activeDot={{ r: 8 }} name="LSTM Forecast" />

                </LineChart>
            </ResponsiveContainer>

            {prediction && prediction.predicted_s !== undefined && (
                <div className="mt-2 text-center">
                    <span className="text-sm font-mono text-purple-400 bg-purple-900/20 px-3 py-1 rounded border border-purple-500/30">
                        🔮 Predicted Next Week: <strong>{prediction.predicted_s}%</strong>
                    </span>
                </div>
            )}
        </div>
    )
}
