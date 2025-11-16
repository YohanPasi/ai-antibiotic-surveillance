import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  fetchAntibiogram,
  fetchIsolate,
  fetchIsolates,
  fetchWardSummary,
} from "./api_mrsa";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell
} from "recharts";

const Card = ({ title, children, icon }) => (
  <div style={{ 
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", 
    borderRadius: 16, 
    boxShadow: "0 8px 32px rgba(102, 126, 234, 0.25)", 
    padding: 24,
    color: "#fff",
    position: "relative",
    overflow: "hidden"
  }}>
    <div style={{ position: "absolute", right: 20, top: 20, fontSize: 48, opacity: 0.2 }}>
      {icon}
    </div>
    <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 8, fontWeight: 500 }}>{title}</div>
    <div style={{ fontSize: 32, fontWeight: 800 }}>{children}</div>
  </div>
);

const StatCard = ({ title, value, subtitle, color = "#667eea" }) => (
  <div style={{ 
    background: "#fff", 
    borderRadius: 12, 
    padding: 20,
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
    borderLeft: `4px solid ${color}`
  }}>
    <div style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>{title}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: "#1e293b", marginBottom: 4 }}>{value}</div>
    {subtitle && <div style={{ fontSize: 12, color: "#94a3b8" }}>{subtitle}</div>}
  </div>
);

const Pill = ({ text, variant = "default" }) => {
  const colors = {
    default: { bg: "#EEF2FF", color: "#4338CA" },
    positive: { bg: "#FEE2E2", color: "#DC2626" },
    negative: { bg: "#DCFCE7", color: "#16A34A" },
    neutral: { bg: "#F1F5F9", color: "#475569" }
  };
  const style = colors[variant];
  return (
    <span style={{ 
      fontSize: 11, 
      padding: "4px 10px", 
      background: style.bg, 
      color: style.color, 
      borderRadius: 12,
      fontWeight: 600
    }}>
      {text}
    </span>
  );
};

export default function MrsaDashboard() {
  const [wardFilter, setWardFilter] = useState(undefined);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [isolates, setIsolates] = useState([]);
  const [total, setTotal] = useState(0);
  const [loadingTable, setLoadingTable] = useState(false);

  const [wardSummary, setWardSummary] = useState([]);
  const [antibiogram, setAntibiogram] = useState([]);
  const [loadingSummary, setLoadingSummary] = useState(true);

  const [detailId, setDetailId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingSummary(true);
        const [ws, ab] = await Promise.all([fetchWardSummary(), fetchAntibiogram()]);
        if (!mounted) return;
        setWardSummary(ws);
        setAntibiogram(ab);
      } catch (error) {
        console.error("Error fetching summary data:", error);
      } finally {
        setLoadingSummary(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingTable(true);
        const { items, total } = await fetchIsolates(page, pageSize, wardFilter);
        if (!mounted) return;
        setIsolates(items);
        setTotal(total);
      } catch (error) {
        console.error("Error fetching isolates:", error);
      } finally {
        setLoadingTable(false);
      }
    })();
    return () => { mounted = false; };
  }, [page, pageSize, wardFilter]);

  const totalIsolates = useMemo(() => wardSummary.reduce((s, x) => s + (x.total || 0), 0), [wardSummary]);
  const totalMrsa = useMemo(() => wardSummary.reduce((s, x) => s + (x.mrsa || 0), 0), [wardSummary]);
  const mrsaRate = useMemo(() => (totalIsolates ? (totalMrsa / totalIsolates) : 0), [totalIsolates, totalMrsa]);

  const wardOptions = useMemo(() => ["All", ...wardSummary.map(x => x.ward || "Unknown")], [wardSummary]);

  async function openDetail(sampleId) {
    setDetailId(sampleId);
    setLoadingDetail(true);
    try {
      const d = await fetchIsolate(sampleId);
      setDetail(d);
    } catch (error) {
      console.error("Error fetching isolate detail:", error);
    } finally {
      setLoadingDetail(false);
    }
  }

  function closeDetail() {
    setDetailId(null);
    setDetail(null);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Color scheme for wards
  const wardColors = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a"];

  return (
    <div style={{ padding: 24, background: "#F1F5F9", minHeight: "100vh", maxWidth: "100vw", boxSizing: "border-box" }}>
      {/* Header */}
      <div style={{ marginBottom: 24, maxWidth: "100%" }}>
        <h1 style={{ fontSize: 28, fontWeight: 900, marginBottom: 6, background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          MRSA Surveillance Dashboard
        </h1>
        <p style={{ color: "#64748b", fontSize: 14 }}>Real-time monitoring of MRSA isolates, resistance patterns, and ward distribution</p>
      </div>

      {/* Key Metrics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16, marginBottom: 24 }}>
        <StatCard 
          title="Total Isolates" 
          value={loadingSummary ? "..." : totalIsolates}
          subtitle="Total samples collected"
          color="#667eea"
        />
        <StatCard 
          title="MRSA Positives" 
          value={loadingSummary ? "..." : totalMrsa}
          subtitle={`${(mrsaRate * 100).toFixed(1)}% of total isolates`}
          color="#dc2626"
        />
        <StatCard 
          title="Overall MRSA Rate" 
          value={loadingSummary ? "..." : `${(mrsaRate * 100).toFixed(1)}%`}
          subtitle={mrsaRate > 0.2 ? "⚠️ Above threshold" : "✓ Within normal range"}
          color={mrsaRate > 0.2 ? "#dc2626" : "#16a34a"}
        />
      </div>

      {/* Charts Section */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 16, marginBottom: 24 }}>
        {/* MRSA Rate by Ward */}
        <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>MRSA Rate by Ward</h3>
          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 16 }}>Percentage of MRSA-positive isolates per ward</p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={wardSummary} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis 
                  dataKey="ward" 
                  angle={-45} 
                  textAnchor="end"
                  height={100}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis 
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "MRSA Rate"]}
                />
                <Bar dataKey="mrsa_rate" radius={[8, 8, 0, 0]}>
                  {wardSummary.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={wardColors[index % wardColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Antibiogram */}
        <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Antibiogram</h3>
          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 16 }}>Percentage of resistant isolates per antibiotic</p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={antibiogram} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis 
                  type="number"
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis 
                  type="category"
                  dataKey="antibiotic"
                  tick={{ fill: "#64748b", fontSize: 11 }}
                />
                <Tooltip 
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "Resistance Rate"]}
                />
                <Bar dataKey="r_rate" radius={[0, 8, 8, 0]}>
                  {antibiogram.map((entry, index) => {
                    const color = entry.r_rate > 0.3 ? "#ef4444" : entry.r_rate > 0.1 ? "#f59e0b" : "#10b981";
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Isolates Table */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 8px rgba(0,0,0,0.06)", width: "100%", maxWidth: "100%", overflowX: "auto", boxSizing: "border-box" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Isolates</h3>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <label style={{ fontSize: 13, color: "#64748b", fontWeight: 500 }}>Filter by Ward:</label>
            <select
              value={wardFilter || "All"}
              onChange={(e) => {
                const val = e.target.value;
                setPage(1);
                setWardFilter(val === "All" ? undefined : val);
              }}
              style={{ 
                padding: "8px 16px", 
                borderRadius: 8, 
                border: "2px solid #e2e8f0",
                fontSize: 14,
                fontWeight: 500,
                cursor: "pointer",
                outline: "none"
              }}
            >
              {wardOptions.map((w) => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ overflowX: "auto", width: "100%" }}>
          <table style={{ width: "100%", minWidth: "700px", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {["Sample ID", "Ward", "Specimen Type", "Collection Time", "MRSA Status", "Actions"].map((h) => (
                  <th key={h} style={{ 
                    padding: "14px 16px", 
                    fontSize: 12, 
                    color: "#64748b", 
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                    textAlign: "left",
                    borderBottom: "2px solid #e2e8f0"
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loadingTable ? (
                <tr>
                  <td colSpan={6} style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
                    Loading isolates...
                  </td>
                </tr>
              ) : isolates.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
                    No isolates found
                  </td>
                </tr>
              ) : isolates.map(row => (
                <tr 
                  key={row.sample_id} 
                  style={{ 
                    borderBottom: "1px solid #f1f5f9",
                    transition: "background 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.closest("tr").style.background = "#f8fafc"}
                  onMouseLeave={(e) => e.target.closest("tr").style.background = "transparent"}
                >
                  <td style={{ padding: "14px 16px", fontWeight: 600, color: "#1e293b" }}>
                    #{row.sample_id}
                  </td>
                  <td style={{ padding: "14px 16px", color: "#475569" }}>
                    {row.ward || <span style={{ color: "#94a3b8" }}>-</span>}
                  </td>
                  <td style={{ padding: "14px 16px", color: "#475569" }}>
                    {row.sample_type || <span style={{ color: "#94a3b8" }}>-</span>}
                  </td>
                  <td style={{ padding: "14px 16px", color: "#475569" }}>
                    {row.collection_time ? format(new Date(row.collection_time), "MMM dd, yyyy HH:mm") : <span style={{ color: "#94a3b8" }}>-</span>}
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    {row.mrsa_label === null ? (
                      <Pill text="Unknown" variant="neutral" />
                    ) : row.mrsa_label ? (
                      <Pill text="MRSA+" variant="positive" />
                    ) : (
                      <Pill text="MRSA−" variant="negative" />
                    )}
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <button
                      onClick={() => openDetail(row.sample_id)}
                      style={{ 
                        padding: "8px 16px", 
                        border: "2px solid #667eea", 
                        borderRadius: 8, 
                        background: "transparent",
                        color: "#667eea",
                        cursor: "pointer",
                        fontWeight: 600,
                        fontSize: 13,
                        transition: "all 0.2s"
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = "#667eea";
                        e.target.style.color = "#fff";
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = "transparent";
                        e.target.style.color = "#667eea";
                      }}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", alignItems: "center", marginTop: 20 }}>
          <button 
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            style={{ 
              padding: "8px 16px", 
              border: "2px solid #e2e8f0", 
              borderRadius: 8, 
              background: page === 1 ? "#f8fafc" : "#fff",
              color: page === 1 ? "#cbd5e1" : "#475569",
              cursor: page === 1 ? "not-allowed" : "pointer",
              fontWeight: 600,
              fontSize: 14
            }}
          >
            Previous
          </button>
          <span style={{ 
            padding: "0 16px", 
            fontSize: 14, 
            color: "#64748b",
            fontWeight: 500
          }}>
            Page {page} of {totalPages}
          </span>
          <button 
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            style={{ 
              padding: "8px 16px", 
              border: "2px solid #e2e8f0", 
              borderRadius: 8, 
              background: page === totalPages ? "#f8fafc" : "#fff",
              color: page === totalPages ? "#cbd5e1" : "#475569",
              cursor: page === totalPages ? "not-allowed" : "pointer",
              fontWeight: 600,
              fontSize: 14
            }}
          >
            Next
          </button>
        </div>
      </div>

      {/* Detail Modal */}
      {detailId !== null && (
        <div
          onClick={closeDetail}
          style={{ 
            position: "fixed", 
            inset: 0, 
            background: "rgba(0,0,0,0.5)", 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "center", 
            padding: 24,
            zIndex: 1000,
            backdropFilter: "blur(4px)"
          }}
        >
          <div 
            onClick={(e) => e.stopPropagation()} 
            style={{ 
              background: "#fff", 
              borderRadius: 20, 
              padding: 32, 
              width: "90%", 
              maxWidth: 900, 
              boxShadow: "0 20px 64px rgba(0,0,0,0.3)",
              maxHeight: "90vh",
              overflowY: "auto"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
              <h2 style={{ fontSize: 24, fontWeight: 800, color: "#1e293b" }}>
                Isolate Details #{detailId}
              </h2>
              <button 
                onClick={closeDetail} 
                style={{ 
                  padding: "8px 16px", 
                  border: "2px solid #e2e8f0", 
                  borderRadius: 8, 
                  background: "#fff", 
                  cursor: "pointer",
                  fontSize: 14,
                  fontWeight: 600,
                  color: "#64748b"
                }}
              >
                ✕ Close
              </button>
            </div>
            {loadingDetail || !detail ? (
              <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>Loading details...</div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24 }}>
                {/* Left Column - Metadata */}
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: "#1e293b" }}>Sample Information</h3>
                  <div style={{ background: "#f8fafc", borderRadius: 12, padding: 20 }}>
                    {[
                      { label: "Ward", value: detail.isolate.ward || "-" },
                      { label: "Sample Type", value: detail.isolate.sample_type || "-" },
                      { label: "Collection Time", value: detail.isolate.collection_time ? format(new Date(detail.isolate.collection_time), "MMM dd, yyyy HH:mm") : "-" },
                      { label: "Organism", value: detail.isolate.organism || "-" },
                      { 
                        label: "mecA Gene", 
                        value: detail.isolate.mecA === null ? "-" : (
                          <Pill text={detail.isolate.mecA ? "Positive" : "Negative"} variant={detail.isolate.mecA ? "positive" : "negative"} />
                        )
                      },
                      { 
                        label: "MRSA Label", 
                        value: detail.isolate.mrsa_label === null ? "-" : (
                          <Pill text={detail.isolate.mrsa_label ? "MRSA+" : "MRSA−"} variant={detail.isolate.mrsa_label ? "positive" : "negative"} />
                        )
                      },
                    ].map((item, idx) => (
                      <div key={idx} style={{ marginBottom: 16, borderBottom: idx < 5 ? "1px solid #e2e8f0" : "none", paddingBottom: idx < 5 ? 16 : 0 }}>
                        <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4, fontWeight: 600, textTransform: "uppercase" }}>
                          {item.label}
                        </div>
                        <div style={{ fontSize: 15, color: "#1e293b", fontWeight: 500 }}>
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right Column - AST & Features */}
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, color: "#1e293b" }}>Antimicrobial Susceptibility</h3>
                  <div style={{ maxHeight: 280, overflow: "auto", background: "#f8fafc", borderRadius: 12, padding: 16 }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr>
                          <th style={{ padding: "10px", fontSize: 12, color: "#64748b", fontWeight: 600, textAlign: "left", borderBottom: "2px solid #e2e8f0" }}>
                            Antibiotic
                          </th>
                          <th style={{ padding: "10px", fontSize: 12, color: "#64748b", fontWeight: 600, textAlign: "center", borderBottom: "2px solid #e2e8f0" }}>
                            Result
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.ast.map(a => (
                          <tr key={a.antibiotic} style={{ borderBottom: "1px solid #e2e8f0" }}>
                            <td style={{ padding: "12px 10px", fontSize: 13, color: "#475569" }}>{a.antibiotic}</td>
                            <td style={{ padding: "12px 10px", textAlign: "center" }}>
                              <Pill 
                                text={a.sir} 
                                variant={a.sir === "R" ? "positive" : a.sir === "S" ? "negative" : "default"} 
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div style={{ marginTop: 20 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: "#1e293b" }}>Feature Snapshots</h3>
                    {detail.features.map(f => (
                      <div key={f.light_stage} style={{ 
                        background: "#f8fafc", 
                        borderRadius: 8, 
                        padding: 12, 
                        marginBottom: 8,
                        fontSize: 13
                      }}>
                        <Pill text={f.light_stage} /> 
                        <div style={{ marginTop: 8, color: "#64748b" }}>
                          <span style={{ fontWeight: 600 }}>Ward:</span> {f.ward || "-"} • {" "}
                          <span style={{ fontWeight: 600 }}>Type:</span> {f.sample_type || "-"} • {" "}
                          <span style={{ fontWeight: 600 }}>Gram:</span> {f.gram || "-"} • {" "}
                          <span style={{ fontWeight: 600 }}>Hour:</span> {f.hour_of_day === null ? "-" : `${f.hour_of_day}:00`}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
