import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  fetchStrepAntibiogram,
  fetchStrepIsolate,
  fetchStrepIsolates,
  fetchStrepWardSummary,
} from "./api_strep";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Cell
} from "recharts";

// ======================
// SMALL REUSABLE UI ITEMS
// ======================
const StatCard = ({ title, value, subtitle, color = "#2563eb" }) => (
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
    default: { bg: "#e2e8f0", color: "#475569" },
    positive: { bg: "#fee2e2", color: "#dc2626" },
    negative: { bg: "#dcfce7", color: "#16a34a" },
    neutral: { bg: "#f1f5f9", color: "#64748b" }
  };
  const c = colors[variant];
  return (
    <span style={{
      fontSize: 11,
      padding: "4px 10px",
      background: c.bg,
      color: c.color,
      borderRadius: 12,
      fontWeight: 600
    }}>
      {text}
    </span>
  );
};

// ======================
// MAIN COMPONENT
// ======================
export default function StrepDashboard() {

  // Filters + Pagination
  const [wardFilter, setWardFilter] = useState(undefined);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Main data
  const [isolates, setIsolates] = useState([]);
  const [total, setTotal] = useState(0);
  const [loadingTable, setLoadingTable] = useState(false);

  const [wardSummary, setWardSummary] = useState([]);
  const [antibiogram, setAntibiogram] = useState([]);
  const [loadingSummary, setLoadingSummary] = useState(true);

  // Detail modal
  const [detailId, setDetailId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);


  // Load summary (Ward + Antibiogram)
  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        setLoadingSummary(true);
        const [ws, ab] = await Promise.all([
          fetchStrepWardSummary(),
          fetchStrepAntibiogram()
        ]);

        if (!mounted) return;
        setWardSummary(ws);
        setAntibiogram(ab);

      } catch (err) {
        console.error("Strep summary error:", err);
      } finally {
        setLoadingSummary(false);
      }
    })();

    return () => { mounted = false; };
  }, []);


  // Load isolates table
  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        setLoadingTable(true);

        const { items, total } = await fetchStrepIsolates(
          page,
          pageSize,
          wardFilter
        );

        if (!mounted) return;

        setIsolates(items);
        setTotal(total);

      } catch (err) {
        console.error("Strep isolates error:", err);
      } finally {
        setLoadingTable(false);
      }
    })();

    return () => { mounted = false; };
  }, [page, pageSize, wardFilter]);


  // Summary stats
  const totalIsolates = wardSummary.reduce((a, b) => a + (b.total || 0), 0);

  // Ward dropdown list
  const wardOptions = ["All", ...wardSummary.map((x) => x.ward || "Unknown")];


  // Open modal
  async function openDetail(id) {
    setDetailId(id);
    setLoadingDetail(true);

    try {
      const d = await fetchStrepIsolate(id);
      setDetail(d);
    } catch (e) {
      console.error("Strep isolate detail error:", e);
    } finally {
      setLoadingDetail(false);
    }
  }

  function closeDetail() {
    setDetailId(null);
    setDetail(null);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const chartColors = ["#2563eb", "#4f46e5", "#7c3aed", "#0ea5e9", "#22c55e", "#f43f5e"];


  // ======================
  // RETURN UI
  // ======================
  return (
    <div style={{ padding: 24, background: "#f1f5f9", minHeight: "100vh" }}>

      {/* HEADER */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{
          fontSize: 28,
          fontWeight: 900,
          marginBottom: 6,
          background: "linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent"
        }}>
          Streptococcus Dashboard
        </h1>
        <p style={{ color: "#64748b", fontSize: 14 }}>
          Distribution of Streptococcus isolates and resistance trends
        </p>
      </div>


      {/* STAT CARDS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px,1fr))", gap: 16, marginBottom: 24 }}>
        <StatCard title="Total Streptococcus Isolates" value={loadingSummary ? "…" : totalIsolates} color="#2563eb" />
        <StatCard title="Detected Wards" value={wardSummary.length} subtitle="Ward distribution" color="#7c3aed" />
      </div>


      {/* CHARTS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px,1fr))", gap: 16, marginBottom: 24 }}>

        {/* Ward Bar Chart */}
        <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 6px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Ward Distribution</h3>
          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>Number of isolates per ward</p>

          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={wardSummary}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="ward" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                  {wardSummary.map((_, i) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Antibiogram */}
        <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 6px rgba(0,0,0,0.06)" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Antibiogram</h3>
          <p style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>Resistance rate (%)</p>

          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={antibiogram} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                <YAxis type="category" dataKey="antibiotic" tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                <Bar dataKey="r_rate" radius={[0, 6, 6, 0]}>
                  {antibiogram.map((ab, i) => {
                    const color = ab.r_rate > 0.3 ? "#ef4444" : "#22c55e";
                    return <Cell key={i} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>


      {/* TABLE */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 16, boxShadow: "0 2px 6px rgba(0,0,0,0.06)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>Isolates</h3>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <label style={{ color: "#475569", fontSize: 14 }}>Filter ward:</label>
            <select
              value={wardFilter || "All"}
              onChange={(e) => {
                const val = e.target.value;
                setPage(1);
                setWardFilter(val === "All" ? undefined : val);
              }}
              style={{
                padding: "6px 12px",
                borderRadius: 8,
                border: "1px solid #cbd5e1"
              }}
            >
              {wardOptions.map((w) => (
                <option key={w}>{w}</option>
              ))}
            </select>
          </div>
        </div>


        {/* Table */}
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["ID", "Ward", "Specimen", "Collection Time", "Actions"].map((h) => (
                <th key={h} style={{
                  padding: "12px 14px",
                  borderBottom: "1px solid #e2e8f0",
                  fontSize: 12,
                  fontWeight: 700,
                  color: "#475569",
                  textAlign: "left"
                }}>{h}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {loadingTable ? (
              <tr>
                <td colSpan="5" style={{ padding: 40, textAlign: "center", color: "#64748b" }}>Loading…</td>
              </tr>
            ) : isolates.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ padding: 40, textAlign: "center", color: "#64748b" }}>No data</td>
              </tr>
            ) : isolates.map((row) => (
              <tr key={row.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                <td style={{ padding: "12px 14px" }}>#{row.sample_id}</td>
                <td style={{ padding: "12px 14px" }}>{row.ward || "-"}</td>
                <td style={{ padding: "12px 14px" }}>{row.sample_type || "-"}</td>
                <td style={{ padding: "12px 14px" }}>
                  {row.collection_time ? format(new Date(row.collection_time), "MMM dd, yyyy HH:mm") : "-"}
                </td>
                <td style={{ padding: "12px 14px" }}>
                  <button
                    onClick={() => openDetail(row.id)}
                    style={{
                      padding: "6px 12px",
                      border: "1px solid #2563eb",
                      borderRadius: 8,
                      background: "transparent",
                      color: "#2563eb",
                      cursor: "pointer",
                      fontWeight: 600,
                      transition: "0.2s"
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>


        {/* Pagination */}
        <div style={{
          display: "flex",
          justifyContent: "flex-end",
          gap: 10,
          marginTop: 20
        }}>
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            style={{
              padding: "6px 12px",
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              cursor: page === 1 ? "not-allowed" : "pointer",
              opacity: page === 1 ? 0.5 : 1
            }}
          >
            Prev
          </button>
          <span style={{ paddingTop: 6 }}>Page {page} / {totalPages}</span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            style={{
              padding: "6px 12px",
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              cursor: page === totalPages ? "not-allowed" : "pointer",
              opacity: page === totalPages ? 0.5 : 1
            }}
          >
            Next
          </button>
        </div>

      </div>


      {/* DETAIL MODAL */}
      {detailId !== null && (
        <div
          onClick={closeDetail}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: 20,
            backdropFilter: "blur(2px)"
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#fff",
              borderRadius: 16,
              padding: 24,
              width: "90%",
              maxWidth: 800,
              maxHeight: "90vh",
              overflowY: "auto"
            }}
          >

            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
              <h2 style={{ fontSize: 22, fontWeight: 700 }}>
                Streptococcus Isolate #{detailId}
              </h2>

              <button
                onClick={closeDetail}
                style={{
                  padding: "6px 12px",
                  border: "1px solid #cbd5e1",
                  borderRadius: 8
                }}
              >
                Close
              </button>
            </div>

            {loadingDetail || !detail ? (
              <div>Loading…</div>
            ) : (
              <>
                {/* Meta */}
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>Metadata</h3>
                  <p><b>Ward:</b> {detail.isolate.ward}</p>
                  <p><b>Specimen Type:</b> {detail.isolate.sample_type}</p>
                  <p><b>Organism:</b> {detail.isolate.organism}</p>
                </div>

                {/* AST */}
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>AST Results</h3>
                  <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 10 }}>
                    <thead>
                      <tr style={{ background: "#f8fafc" }}>
                        <th style={{ padding: 10, borderBottom: "1px solid #e2e8f0", textAlign: "left" }}>Antibiotic</th>
                        <th style={{ padding: 10, borderBottom: "1px solid #e2e8f0" }}>Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.ast.map(a => (
                        <tr key={a.antibiotic}>
                          <td style={{ padding: 10 }}>{a.antibiotic}</td>
                          <td style={{ padding: 10, textAlign: "center" }}>
                            <Pill
                              text={a.result}
                              variant={a.result === "R" ? "positive" : a.result === "S" ? "negative" : "default"}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

              </>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
