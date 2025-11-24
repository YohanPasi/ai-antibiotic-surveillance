import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type WeeklyPoint = {
  week_start: string;
  total: number;
  mrsa_count: number;
  mrsa_rate: number;
  avg_probability: number;
};

type RecentPrediction = {
  id: number;
  sample_id: string | null;
  ward: string | null;
  sample_type: string | null;
  organism: string | null;
  gram: string | null;
  model_type: string;
  probability: number;
  predicted_label: number;
  created_at: string;
};

type HighRiskAlert = RecentPrediction;

const MrsaDashboard: React.FC = () => {
  const [weekly, setWeekly] = useState<WeeklyPoint[]>([]);
  const [recent, setRecent] = useState<RecentPrediction[]>([]);
  const [alerts, setAlerts] = useState<HighRiskAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const baseUrl = "http://127.0.0.1:8000"; // adjust if you have a proxy

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [weeklyRes, recentRes, alertRes] = await Promise.all([
          fetch(`${baseUrl}/mrsa/dashboard/weekly_trend?weeks=8`),
          fetch(`${baseUrl}/mrsa/dashboard/recent?limit=50`),
          fetch(`${baseUrl}/mrsa/dashboard/high_risk?threshold=0.8&days=14`),
        ]);

        const weeklyJson = await weeklyRes.json();
        const recentJson = await recentRes.json();
        const alertJson = await alertRes.json();

        setWeekly(weeklyJson.points || []);
        setRecent(recentJson.items || []);
        setAlerts(alertJson.items || []);
      } catch (err) {
        console.error("Error loading MRSA dashboard", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-4">
          MRSA Early-Risk Dashboard
        </h1>
        <p>Loading data...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">
            MRSA Early-Risk Surveillance
          </h1>
          <p className="text-sm text-gray-500">
            Weekly predicted MRSA risk, high-risk alerts, and latest
            predictions from the model.
          </p>
        </div>
      </header>

      {/* Weekly Trend */}
      <section className="bg-white rounded-2xl shadow p-4">
        <h2 className="text-lg font-semibold mb-2">
          Weekly Predicted MRSA Rate (Last 8 Weeks)
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          MRSA rate = predicted MRSA / total predictions per week.
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weekly}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week_start" />
              <YAxis
                domain={[0, 1]}
                tickFormatter={(v) => `${Math.round(v * 100)}%`}
              />
              <Tooltip
                formatter={(value: any, name: any) => {
                  if (name === "mrsa_rate") {
                    return [`${Math.round(value * 100)}%`, "MRSA rate"];
                  }
                  if (name === "avg_probability") {
                    return [value.toFixed(2), "Avg probability"];
                  }
                  return [value, name];
                }}
              />
              <Line
                type="monotone"
                dataKey="mrsa_rate"
                strokeWidth={2}
                dot={false}
                name="MRSA rate"
              />
              <Line
                type="monotone"
                dataKey="avg_probability"
                strokeWidth={2}
                dot={false}
                name="Avg probability"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High-Risk Alerts */}
        <section className="bg-white rounded-2xl shadow p-4">
          <h2 className="text-lg font-semibold mb-2">High-Risk Alerts</h2>
          <p className="text-xs text-gray-500 mb-3">
            Predictions with probability ≥ 0.8 in last 14 days.
          </p>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-500">No high-risk alerts.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-1 pr-2">Time</th>
                    <th className="text-left py-1 pr-2">Sample</th>
                    <th className="text-left py-1 pr-2">Ward</th>
                    <th className="text-left py-1 pr-2">Specimen</th>
                    <th className="text-left py-1 pr-2">Organism</th>
                    <th className="text-left py-1 pr-2">Model</th>
                    <th className="text-right py-1 pl-2">Prob</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((a) => (
                    <tr key={a.id} className="border-b last:border-0">
                      <td className="py-1 pr-2">
                        {new Date(a.created_at).toLocaleString()}
                      </td>
                      <td className="py-1 pr-2">{a.sample_id || "-"}</td>
                      <td className="py-1 pr-2">{a.ward || "-"}</td>
                      <td className="py-1 pr-2">{a.sample_type || "-"}</td>
                      <td className="py-1 pr-2">{a.organism || "-"}</td>
                      <td className="py-1 pr-2 text-xs uppercase">
                        {a.model_type}
                      </td>
                      <td className="py-1 pl-2 text-right font-semibold">
                        {a.probability.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Recent Predictions Timeline */}
        <section className="bg-white rounded-2xl shadow p-4">
          <h2 className="text-lg font-semibold mb-2">Recent Predictions</h2>
          <p className="text-xs text-gray-500 mb-3">
            Latest 50 MRSA predictions from both Light-1 and Light-4 models.
          </p>
          {recent.length === 0 ? (
            <p className="text-sm text-gray-500">No predictions yet.</p>
          ) : (
            <div className="overflow-x-auto max-h-80">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-1 pr-2">Time</th>
                    <th className="text-left py-1 pr-2">Sample</th>
                    <th className="text-left py-1 pr-2">Ward</th>
                    <th className="text-left py-1 pr-2">Specimen</th>
                    <th className="text-left py-1 pr-2">Organism</th>
                    <th className="text-left py-1 pr-2">Model</th>
                    <th className="text-right py-1 pl-2">Label</th>
                    <th className="text-right py-1 pl-2">Prob</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((r) => (
                    <tr key={r.id} className="border-b last:border-0">
                      <td className="py-1 pr-2">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="py-1 pr-2">{r.sample_id || "-"}</td>
                      <td className="py-1 pr-2">{r.ward || "-"}</td>
                      <td className="py-1 pr-2">{r.sample_type || "-"}</td>
                      <td className="py-1 pr-2">{r.organism || "-"}</td>
                      <td className="py-1 pr-2 text-xs uppercase">
                        {r.model_type}
                      </td>
                      <td className="py-1 pl-2 text-right">
                        {r.predicted_label === 1 ? "MRSA" : "MSSA"}
                      </td>
                      <td className="py-1 pl-2 text-right">
                        {r.probability.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default MrsaDashboard;
