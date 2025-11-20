// NonfermenterDashboard.jsx
import { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  fetchNF_Antibiogram,
  fetchNF_IsolateDetail,
  fetchNF_Isolates,
  fetchNF_WardSummary,
} from "./api_nonfermenter";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
} from "recharts";

const StatCard = ({ title, value, subtitle, color = "#0f766e" }) => (
  <div
    style={{
      background: "#fff",
      borderRadius: 12,
      padding: 20,
      boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
      borderLeft: `4px solid ${color}`,
    }}
  >
    <div style={{ fontSize: 13, color: "#64748b", marginBottom: 8 }}>{title}</div>
    <div
      style={{
        fontSize: 28,
        fontWeight: 700,
        color: "#0f172a",
        marginBottom: 4,
      }}
    >
      {value}
    </div>
    {subtitle && (
      <div style={{ fontSize: 12, color: "#94a3b8" }}>{subtitle}</div>
    )}
  </div>
);

const Pill = ({ text, variant = "default" }) => {
  const colors = {
    default: { bg: "#e0f2fe", color: "#0ea5e9" },
    positive: { bg: "#fee2e2", color: "#dc2626" }, // resistant / “bad”
    negative: { bg: "#dcfce7", color: "#16a34a" }, // susceptible / “good”
    neutral: { bg: "#f1f5f9", color: "#475569" },
  };
  const style = colors[variant] || colors.default;
  return (
    <span
      style={{
        fontSize: 11,
        padding: "4px 10px",
        background: style.bg,
        color: style.color,
        borderRadius: 12,
        fontWeight: 600,
      }}
    >
      {text}
    </span>
  );
};

export default function NonfermenterDashboard() {
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

  // Load summary (ward + antibiogram)
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingSummary(true);
        const [ws, ab] = await Promise.all([
          fetchNF_WardSummary(),
          fetchNF_Antibiogram(),
        ]);
        if (!mounted) return;
        setWardSummary(ws || []);
        setAntibiogram(ab || []);
      } catch (e) {
        console.error("Error fetching NF summary:", e);
      } finally {
        setLoadingSummary(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Load isolates table
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingTable(true);
        const { items, total } = await fetchNF_Isolates(
          page,
          pageSize,
          wardFilter
        );
        if (!mounted) return;
        setIsolates(items || []);
        setTotal(total || 0);
      } catch (e) {
        console.error("Error fetching NF isolates:", e);
      } finally {
        setLoadingTable(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [page, pageSize, wardFilter]);

  const totalIsolates = useMemo(
    () => wardSummary.reduce((s, x) => s + (x.total || 0), 0),
    [wardSummary]
  );
  const totalCR = useMemo(
    () => wardSummary.reduce((s, x) => s + (x.cr || 0), 0),
    [wardSummary]
  );
  const crRate = useMemo(
    () => (totalIsolates ? totalCR / totalIsolates : 0),
    [totalIsolates, totalCR]
  );

  const wardOptions = useMemo(
    () => ["All", ...wardSummary.map((x) => x.ward || "Unknown")],
    [wardSummary]
  );

  async function openDetail(isolateId) {
    setDetailId(isolateId);
    setLoadingDetail(true);
    try {
      const d = await fetchNF_IsolateDetail(isolateId);
      setDetail(d);
    } catch (e) {
      console.error("Error fetching NF isolate detail:", e);
    } finally {
      setLoadingDetail(false);
    }
  }

  function closeDetail() {
    setDetailId(null);
    setDetail(null);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const wardColors = ["#0f766e", "#14b8a6", "#06b6d4", "#0ea5e9", "#6366f1", "#22c55e"];

  return (
    <div
      style={{
        padding: 24,
        background: "#f1f5f9",
        minHeight: "100vh",
        maxWidth: "100vw",
        boxSizing: "border-box",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 24, maxWidth: "100%" }}>
        <h1
          style={{
            fontSize: 28,
            fontWeight: 900,
            marginBottom: 6,
            background: "linear-gradient(135deg, #0f766e 0%, #0ea5e9 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Non-fermenter Surveillance Dashboard
        </h1>
        <p style={{ color: "#64748b", fontSize: 14 }}>
          Monitoring non-fermenter isolates, carbapenem resistance, and ward
          patterns
        </p>
      </div>

      {/* Key metrics */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <StatCard
          title="Total Non-fermenter Isolates"
          value={loadingSummary ? "..." : totalIsolates}
          subtitle="Total isolates included in this module"
          color="#0f766e"
        />
        <StatCard
          title="Carbapenem-resistant (CR) isolates"
          value={loadingSummary ? "..." : totalCR}
          subtitle={`${(crRate * 100).toFixed(1)}% of total isolates`}
          color="#dc2626"
        />
        <StatCard
          title="Overall CR rate"
          value={loadingSummary ? "..." : `${(crRate * 100).toFixed(1)}%`}
          subtitle={
            crRate > 0.2
              ? "⚠️ High carbapenem resistance burden"
              : "✓ Within expected range"
          }
          color={crRate > 0.2 ? "#dc2626" : "#16a34a"}
        />
      </div>

      {/* Charts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        {/* CR rate by ward */}
        <div
          style={{
            background: "#fff",
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
            Carbapenem-resistant (CR) rate by ward
          </h3>
          <p
            style={{
              fontSize: 12,
              color: "#64748b",
              marginBottom: 16,
            }}
          >
            Percentage of non-fermenter isolates that are carbapenem-resistant
            per ward
          </p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart
                data={wardSummary}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
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
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e2e8f0",
                  }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "CR rate"]}
                />
                <Bar dataKey="cr_rate" radius={[8, 8, 0, 0]}>
                  {wardSummary.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={wardColors[index % wardColors.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Antibiogram */}
        <div
          style={{
            background: "#fff",
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>
            Antibiogram (R rate)
          </h3>
          <p
            style={{
              fontSize: 12,
              color: "#64748b",
              marginBottom: 16,
            }}
          >
            Percentage of resistant non-fermenter isolates per antibiotic
          </p>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart
                data={antibiogram}
                layout="vertical"
                margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
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
                  contentStyle={{
                    borderRadius: 12,
                    border: "1px solid #e2e8f0",
                  }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "Resistance"]}
                />
                <Bar dataKey="r_rate" radius={[0, 8, 8, 0]}>
                  {antibiogram.map((entry, index) => {
                    const r = entry.r_rate || 0;
                    const color =
                      r > 0.3 ? "#ef4444" : r > 0.1 ? "#f59e0b" : "#10b981";
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Isolates table */}
      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 16,
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          width: "100%",
          maxWidth: "100%",
          overflowX: "auto",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 16,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <h3 style={{ fontSize: 16, fontWeight: 700 }}>
            Non-fermenter isolates
          </h3>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <label
              style={{
                fontSize: 13,
                color: "#64748b",
                fontWeight: 500,
              }}
            >
              Filter by ward:
            </label>
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
                outline: "none",
              }}
            >
              {wardOptions.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ overflowX: "auto", width: "100%" }}>
          <table
            style={{
              width: "100%",
              minWidth: "700px",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {[
                  "ID",
                  "Sample ID",
                  "Ward",
                  "Specimen Type",
                  "Collection Time",
                  "CR Status",
                  "Actions",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "14px 16px",
                      fontSize: 12,
                      color: "#64748b",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                      textAlign: "left",
                      borderBottom: "2px solid #e2e8f0",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loadingTable ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: 40,
                      textAlign: "center",
                      color: "#94a3b8",
                    }}
                  >
                    Loading isolates...
                  </td>
                </tr>
              ) : isolates.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: 40,
                      textAlign: "center",
                      color: "#94a3b8",
                    }}
                  >
                    No isolates found
                  </td>
                </tr>
              ) : (
                isolates.map((row) => (
                  <tr
                    key={row.id}
                    style={{
                      borderBottom: "1px solid #f1f5f9",
                      transition: "background 0.2s",
                    }}
                    onMouseEnter={(e) =>
                      (e.target.closest("tr").style.background = "#f8fafc")
                    }
                    onMouseLeave={(e) =>
                      (e.target.closest("tr").style.background = "transparent")
                    }
                  >
                    <td
                      style={{
                        padding: "14px 16px",
                        fontWeight: 600,
                        color: "#0f172a",
                      }}
                    >
                      #{row.id}
                    </td>
                    <td
                      style={{
                        padding: "14px 16px",
                        color: "#0f172a",
                      }}
                    >
                      {row.sample_id ?? <span style={{ color: "#94a3b8" }}>-</span>}
                    </td>
                    <td
                      style={{ padding: "14px 16px", color: "#475569" }}
                    >
                      {row.ward || <span style={{ color: "#94a3b8" }}>-</span>}
                    </td>
                    <td
                      style={{ padding: "14px 16px", color: "#475569" }}
                    >
                      {row.sample_type || (
                        <span style={{ color: "#94a3b8" }}>-</span>
                      )}
                    </td>
                    <td
                      style={{ padding: "14px 16px", color: "#475569" }}
                    >
                      {row.collection_time ? (
                        format(
                          new Date(row.collection_time),
                          "MMM dd, yyyy HH:mm"
                        )
                      ) : (
                        <span style={{ color: "#94a3b8" }}>-</span>
                      )}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      {row.carbapenem_resistant == null ? (
                        <Pill text="Unknown" variant="neutral" />
                      ) : row.carbapenem_resistant ? (
                        <Pill text="CR+" variant="positive" />
                      ) : (
                        <Pill text="CR−" variant="negative" />
                      )}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      <button
                        onClick={() => openDetail(row.id)}
                        style={{
                          padding: "8px 16px",
                          border: "2px solid #0f766e",
                          borderRadius: 8,
                          background: "transparent",
                          color: "#0f766e",
                          cursor: "pointer",
                          fontWeight: 600,
                          fontSize: 13,
                          transition: "all 0.2s",
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.background = "#0f766e";
                          e.target.style.color = "#fff";
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.background = "transparent";
                          e.target.style.color = "#0f766e";
                        }}
                      >
                        View details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div
          style={{
            display: "flex",
            gap: 8,
            justifyContent: "flex-end",
            alignItems: "center",
            marginTop: 20,
          }}
        >
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
              fontSize: 14,
            }}
          >
            Previous
          </button>
          <span
            style={{
              padding: "0 16px",
              fontSize: 14,
              color: "#64748b",
              fontWeight: 500,
            }}
          >
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
              fontSize: 14,
            }}
          >
            Next
          </button>
        </div>
      </div>

      {/* Detail modal */}
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
            backdropFilter: "blur(4px)",
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
              overflowY: "auto",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 24,
              }}
            >
              <h2
                style={{
                  fontSize: 24,
                  fontWeight: 800,
                  color: "#0f172a",
                }}
              >
                Non-fermenter isolate #{detailId}
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
                  color: "#64748b",
                }}
              >
                ✕ Close
              </button>
            </div>

            {loadingDetail || !detail ? (
              <div
                style={{
                  padding: 40,
                  textAlign: "center",
                  color: "#94a3b8",
                }}
              >
                Loading details...
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                  gap: 24,
                }}
              >
                {/* Left column: meta */}
                <div>
                  <h3
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      marginBottom: 16,
                      color: "#0f172a",
                    }}
                  >
                    Sample information
                  </h3>
                  <div
                    style={{
                      background: "#f8fafc",
                      borderRadius: 12,
                      padding: 20,
                    }}
                  >
                    {[
                      {
                        label: "Sample ID",
                        value: detail.isolate.sample_id ?? "-",
                      },
                      { label: "Ward", value: detail.isolate.ward || "-" },
                      {
                        label: "Sample type",
                        value: detail.isolate.sample_type || "-",
                      },
                      {
                        label: "Collection time",
                        value: detail.isolate.collection_time
                          ? format(
                              new Date(detail.isolate.collection_time),
                              "MMM dd, yyyy HH:mm"
                            )
                          : "-",
                      },
                      {
                        label: "Organism",
                        value: detail.isolate.organism || "-",
                      },
                      {
                        label: "Carbapenem resistance",
                        value:
                          detail.isolate.carbapenem_resistant == null ? (
                            "-"
                          ) : detail.isolate.carbapenem_resistant ? (
                            <Pill text="CR+" variant="positive" />
                          ) : (
                            <Pill text="CR−" variant="negative" />
                          ),
                      },
                    ].map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          marginBottom: 16,
                          borderBottom:
                            idx < 5 ? "1px solid #e2e8f0" : "none",
                          paddingBottom: idx < 5 ? 16 : 0,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 12,
                            color: "#64748b",
                            marginBottom: 4,
                            fontWeight: 600,
                            textTransform: "uppercase",
                          }}
                        >
                          {item.label}
                        </div>
                        <div
                          style={{
                            fontSize: 15,
                            color: "#0f172a",
                            fontWeight: 500,
                          }}
                        >
                          {item.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right column: AST + features */}
                <div>
                  <h3
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      marginBottom: 16,
                      color: "#0f172a",
                    }}
                  >
                    Antimicrobial susceptibility
                  </h3>
                  <div
                    style={{
                      maxHeight: 280,
                      overflow: "auto",
                      background: "#f8fafc",
                      borderRadius: 12,
                      padding: 16,
                    }}
                  >
                    <table
                      style={{ width: "100%", borderCollapse: "collapse" }}
                    >
                      <thead>
                        <tr>
                          <th
                            style={{
                              padding: "10px",
                              fontSize: 12,
                              color: "#64748b",
                              fontWeight: 600,
                              textAlign: "left",
                              borderBottom: "2px solid #e2e8f0",
                            }}
                          >
                            Antibiotic
                          </th>
                          <th
                            style={{
                              padding: "10px",
                              fontSize: 12,
                              color: "#64748b",
                              fontWeight: 600,
                              textAlign: "center",
                              borderBottom: "2px solid #e2e8f0",
                            }}
                          >
                            Result
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.ast.map((a) => (
                          <tr
                            key={a.antibiotic}
                            style={{ borderBottom: "1px solid #e2e8f0" }}
                          >
                            <td
                              style={{
                                padding: "12px 10px",
                                fontSize: 13,
                                color: "#475569",
                              }}
                            >
                              {a.antibiotic}
                            </td>
                            <td
                              style={{
                                padding: "12px 10px",
                                textAlign: "center",
                              }}
                            >
                              <Pill
                                text={a.sir}
                                variant={
                                  a.sir === "R"
                                    ? "positive"
                                    : a.sir === "S"
                                    ? "negative"
                                    : "default"
                                }
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ marginTop: 20 }}>
                    <h3
                      style={{
                        fontSize: 16,
                        fontWeight: 700,
                        marginBottom: 12,
                        color: "#0f172a",
                      }}
                    >
                      Feature snapshots
                    </h3>
                    {detail.features.map((f) => (
                      <div
                        key={f.light_stage}
                        style={{
                          background: "#f8fafc",
                          borderRadius: 8,
                          padding: 12,
                          marginBottom: 8,
                          fontSize: 13,
                        }}
                      >
                        <Pill text={f.light_stage} />
                        <div
                          style={{
                            marginTop: 8,
                            color: "#64748b",
                          }}
                        >
                          <span style={{ fontWeight: 600 }}>Ward:</span>{" "}
                          {f.ward || "-"} •{" "}
                          <span style={{ fontWeight: 600 }}>Type:</span>{" "}
                          {f.sample_type || "-"} •{" "}
                          <span style={{ fontWeight: 600 }}>Gram:</span>{" "}
                          {f.gram || "-"} •{" "}
                          <span style={{ fontWeight: 600 }}>Hour:</span>{" "}
                          {f.hour_of_day == null
                            ? "-"
                            : `${f.hour_of_day}:00`}
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
