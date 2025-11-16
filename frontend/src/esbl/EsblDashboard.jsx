import React, { useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  fetchESBLWardSummary,
  fetchESBLAntibiogram,
  fetchESBLIsolate,
  fetchESBLIsolates,
} from "./api_esbl"; // Assuming api_esbl.js is in the same directory
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell
} from "recharts";

// --- Reusable Components ---

const StatCard = ({ title, value, subtitle, color }) => (
  <div style={{
    background: "#ffffff",
    borderRadius: "16px", // Softer corners
    padding: "24px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.05)", // More subtle shadow
    borderLeft: `6px solid ${color}`, // Thicker accent
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: "120px", // Ensure consistent height
  }}>
    <div style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "8px", fontWeight: 500 }}>
      {title}
    </div>
    <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "#1f2937", lineHeight: 1 }}>
      {value}
    </div>
    <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "4px" }}>
      {subtitle}
    </div>
  </div>
);

const Pill = ({ text, variant }) => {
  const styles = {
    positive: { bg: "#fef2f2", color: "#ef4444" }, // Lighter red
    negative: { bg: "#ecfdf5", color: "#10b981" }, // Lighter green
    neutral: { bg: "#f9fafb", color: "#6b7280" } // Lighter neutral
  }[variant];

  return (
    <span style={{
      padding: "6px 12px",
      borderRadius: "9999px", // Fully rounded
      background: styles.bg,
      color: styles.color,
      fontSize: "0.75rem",
      fontWeight: 600,
      textTransform: "uppercase", // A bit more modern
      letterSpacing: "0.025em",
    }}>
      {text}
    </span>
  );
};

const Button = ({ children, onClick, variant = "primary", style }) => {
  const baseStyles = {
    padding: "10px 18px",
    borderRadius: "10px",
    border: "none",
    cursor: "pointer",
    fontSize: "0.9375rem",
    fontWeight: 600,
    transition: "all 0.2s ease-in-out",
    boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
  };

  const variantStyles = {
    primary: {
      background: "#0ea5e9", // Blue
      color: "#ffffff",
      "&:hover": { background: "#0284c7" },
    },
    secondary: {
      background: "#ffffff",
      color: "#4b5563",
      border: "1px solid #d1d5db",
      "&:hover": { background: "#f3f4f6" },
    },
    danger: {
      background: "#ef4444",
      color: "#ffffff",
      "&:hover": { background: "#dc2626" },
    },
  }[variant];

  return (
    <button
      onClick={onClick}
      style={{ ...baseStyles, ...variantStyles, ...style }}
      onMouseEnter={(e) => {
        if (variantStyles["&:hover"]) {
          Object.assign(e.currentTarget.style, variantStyles["&:hover"]);
        }
      }}
      onMouseLeave={(e) => {
        Object.assign(e.currentTarget.style, variantStyles); // Reset to original variant styles
      }}
    >
      {children}
    </button>
  );
};


// --- Main Dashboard Component ---

export default function EsblDashboard() {
  const [wardFilter, setWardFilter] = useState("All");
  const [isolates, setIsolates] = useState([]);
  const [total, setTotal] = useState(0);
  const [loadingTable, setLoadingTable] = useState(false);

  const [summary, setSummary] = useState([]);
  const [antibiogram, setAntibiogram] = useState([]);

  const [detailId, setDetailId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const pageSize = 10; // Slightly smaller page size for cleaner look
  const [page, setPage] = useState(1);

  // Load summary + antibiogram
  useEffect(() => {
    (async () => {
      try {
        const s = await fetchESBLWardSummary();
        const ab = await fetchESBLAntibiogram();
        setSummary(s || []);
        setAntibiogram(ab || []);
      } catch (error) {
        console.error("Error loading summary/antibiogram:", error);
        setSummary([]);
        setAntibiogram([]);
      }
    })();
  }, []);

  // Load isolates table
  useEffect(() => {
    (async () => {
      setLoadingTable(true);
      try {
        const data = await fetchESBLIsolates(page, pageSize, wardFilter === "All" ? undefined : wardFilter);
        setIsolates(data?.items || []);
        setTotal(data?.total || 0);
      } catch (error) {
        console.error("Error loading isolates:", error);
        setIsolates([]);
        setTotal(0);
      } finally {
        setLoadingTable(false);
      }
    })();
  }, [page, wardFilter]);

  const totalIsolates = useMemo(() => summary.reduce((t, x) => t + x.total, 0), [summary]);
  const totalESBL = useMemo(() => summary.reduce((t, x) => t + x.esbl, 0), [summary]);
  const esblRate = useMemo(() =>
    totalIsolates ? (totalESBL / totalIsolates) : 0
  , [totalIsolates, totalESBL]);

  const wardOptions = ["All", ...summary.map(x => x.ward)];

  const openDetail = async (id) => {
    setDetailId(id);
    setLoadingDetail(true);
    try {
      const res = await fetchESBLIsolate(id);
      setDetail(res);
    } catch (error) {
      console.error("Error loading isolate detail:", error);
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const closeDetail = () => {
    setDetailId(null);
    setDetail(null);
  };

  // Refined color palette for charts and cards
  const dashboardColors = {
    primary: "#0ea5e9", // Sky Blue
    secondary: "#10b981", // Emerald Green
    accent1: "#6366f1", // Indigo
    accent2: "#f59e0b", // Amber
    danger: "#ef4444", // Red
    warning: "#f59e0b", // Orange
    success: "#10b981", // Green
    neutralText: "#4b5563",
    lightBackground: "#f9fafb",
    cardBackground: "#ffffff",
  };

  const wardChartColors = ["#0ea5e9", "#10b981", "#6366f1", "#8b5cf6", "#f59e0b", "#ef4444", "#a855f7"];


  return (
    <div style={{
      fontFamily: "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'",
      padding: "24px",
      background: dashboardColors.lightBackground,
      minHeight: "100vh",
      color: dashboardColors.neutralText,
    }}>
      <h1 style={{
        fontSize: "2.25rem",
        fontWeight: 800,
        background: `linear-gradient(90deg, ${dashboardColors.primary}, ${dashboardColors.secondary})`,
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        marginBottom: "8px",
      }}>
        ESBL Surveillance Dashboard
      </h1>
      <p style={{ color: "#6b7280", marginBottom: "32px", fontSize: "1rem" }}>
        Live monitoring of ESBL-positive isolates, ward distribution, and resistance trends.
      </p>

      {/* STAT CARDS */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", // Slightly wider min for cards
        gap: "20px", // More spacing
        marginBottom: "32px",
      }}>
        <StatCard
          title="Total Isolates"
          value={totalIsolates}
          subtitle="All samples processed"
          color={dashboardColors.primary}
        />
        <StatCard
          title="ESBL Positives"
          value={totalESBL}
          subtitle={`${(esblRate * 100).toFixed(1)}% of isolates`}
          color={dashboardColors.danger}
        />
        <StatCard
          title="Overall ESBL Rate"
          value={`${(esblRate * 100).toFixed(1)}%`}
          subtitle={esblRate > 0.25 ? "⚠ High prevalence, immediate action needed" : "Within normal prevalence range"}
          color={esblRate > 0.25 ? dashboardColors.danger : dashboardColors.success}
        />
      </div>

      {/* CHARTS */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
        gap: "20px",
        marginBottom: "32px",
      }}>

        {/* Ward ESBL Rate */}
        <div style={{
          background: dashboardColors.cardBackground,
          borderRadius: "16px",
          padding: "24px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
        }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#1f2937", marginBottom: "16px" }}>
            ESBL Rate by Ward
          </h3>
          <div style={{ width: "100%", height: 300 }}> {/* Increased chart height */}
            <ResponsiveContainer>
              <BarChart data={summary} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="ward" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                <YAxis
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                  contentStyle={{
                    borderRadius: "8px",
                    border: "none",
                    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
                    fontSize: "0.875rem",
                  }}
                  itemStyle={{ color: "#1f2937" }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "ESBL Rate"]}
                  labelFormatter={(label) => `Ward: ${label}`}
                />
                <Bar dataKey="esbl_rate" radius={[8, 8, 0, 0]}>
                  {summary.map((_, i) => (
                    <Cell key={`cell-${i}`} fill={wardChartColors[i % wardChartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Antibiogram */}
        <div style={{
          background: dashboardColors.cardBackground,
          borderRadius: "16px",
          padding: "24px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
        }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#1f2937", marginBottom: "16px" }}>
            Antibiogram (Resistance %)
          </h3>
          <div style={{ width: "100%", height: 300 }}> {/* Increased chart height */}
            <ResponsiveContainer>
              <BarChart data={antibiogram} layout="vertical" margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey="antibiotic"
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                  width={80} // Adjust width for antibiotic names
                />
                <Tooltip
                  cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                  contentStyle={{
                    borderRadius: "8px",
                    border: "none",
                    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
                    fontSize: "0.875rem",
                  }}
                  itemStyle={{ color: "#1f2937" }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`, "Resistance Rate"]}
                  labelFormatter={(label) => `Antibiotic: ${label}`}
                />
                <Bar dataKey="r_rate" radius={[0, 8, 8, 0]}>
                  {antibiogram.map((a, i) => (
                    <Cell
                      key={`cell-${i}`}
                      fill={a.r_rate > 0.5 ? dashboardColors.danger : a.r_rate > 0.25 ? dashboardColors.warning : dashboardColors.success}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* TABLE */}
      <div style={{
        background: dashboardColors.cardBackground,
        padding: "24px",
        borderRadius: "16px",
        boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          flexWrap: "wrap", // For responsiveness
          gap: "12px",
        }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#1f2937" }}>
            Isolates
          </h3>

          <select
            value={wardFilter}
            onChange={(e) => {
              setPage(1);
              setWardFilter(e.target.value);
            }}
            style={{
              padding: "10px 14px",
              borderRadius: "10px",
              border: "1px solid #d1d5db",
              background: "#ffffff",
              fontSize: "0.9375rem",
              color: dashboardColors.neutralText,
              outline: "none",
              cursor: "pointer",
            }}
          >
            {wardOptions.map(w => <option key={w} value={w}>{w}</option>)}
          </select>
        </div>

        <div style={{ overflowX: "auto" }}> {/* Make table horizontally scrollable */}
          <table style={{
            width: "100%",
            borderCollapse: "separate", // For rounded corners on rows
            borderSpacing: "0 8px", // Space between rows
            marginBottom: "16px",
          }}>
            <thead style={{ background: "#f8fafc" }}>
              <tr>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                  borderTopLeftRadius: "10px", // Rounded corners for header
                  borderBottomLeftRadius: "10px",
                }}>Sample ID</th>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                }}>Ward</th>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                }}>Organism</th>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                }}>Specimen</th>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "left",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                }}>ESBL</th>
                <th style={{
                  padding: "12px 16px",
                  textAlign: "center",
                  color: "#6b7280",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  borderBottom: "1px solid #e5e7eb",
                  borderTopRightRadius: "10px", // Rounded corners for header
                  borderBottomRightRadius: "10px",
                }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loadingTable ? (
                <tr>
                  <td colSpan={6} style={{ padding: "20px", textAlign: "center", color: "#6b7280" }}>
                    Loading isolates...
                  </td>
                </tr>
              ) : isolates.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "20px", textAlign: "center", color: "#6b7280" }}>
                    No isolates found for the current filter.
                  </td>
                </tr>
              ) : (
                isolates.map(row => (
                  <tr
                    key={row.sample_id}
                    style={{
                      background: "#ffffff",
                      boxShadow: "0 1px 5px rgba(0,0,0,0.03)",
                      borderRadius: "10px",
                      cursor: "pointer",
                      transition: "transform 0.1s ease-in-out, box-shadow 0.1s ease-in-out",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = "translateY(-2px)";
                      e.currentTarget.style.boxShadow = "0 4px 10px rgba(0,0,0,0.08)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "translateY(0)";
                      e.currentTarget.style.boxShadow = "0 1px 5px rgba(0,0,0,0.03)";
                    }}
                  >
                    <td style={{ padding: "12px 16px", borderTopLeftRadius: "10px", borderBottomLeftRadius: "10px", fontSize: "0.9375rem" }}>
                      <span style={{ fontWeight: 600, color: dashboardColors.primary }}>#{row.sample_id}</span>
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: "0.9375rem" }}>{row.ward || "-"}</td>
                    <td style={{ padding: "12px 16px", fontSize: "0.9375rem" }}>{row.organism || "-"}</td>
                    <td style={{ padding: "12px 16px", fontSize: "0.9375rem" }}>{row.sample_type || "-"}</td>
                    <td style={{ padding: "12px 16px", fontSize: "0.9375rem" }}>
                      {row.esbl_label
                        ? <Pill text="ESBL Positive" variant="positive" />
                        : <Pill text="ESBL Negative" variant="negative" />
                      }
                    </td>
                    <td style={{ padding: "12px 16px", textAlign: "center", borderTopRightRadius: "10px", borderBottomRightRadius: "10px" }}>
                      <Button variant="secondary" onClick={() => openDetail(row.sample_id)}>
                        View Details
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION */}
        <div style={{
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          gap: "12px",
          marginTop: "20px",
          flexWrap: "wrap",
        }}>
          <Button
            variant="secondary"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={page === 1 ? { opacity: 0.6, cursor: "not-allowed" } : {}}
          >
            Previous
          </Button>
          <span style={{ fontSize: "1rem", fontWeight: 500, color: dashboardColors.neutralText }}>
            Page {page} of {Math.ceil(total / pageSize)}
          </span>
          <Button
            variant="secondary"
            onClick={() => setPage(p => p + 1)}
            disabled={page * pageSize >= total}
            style={page * pageSize >= total ? { opacity: 0.6, cursor: "not-allowed" } : {}}
          >
            Next
          </Button>
        </div>
      </div>

      {/* DETAIL MODAL */}
      {detailId && (
        <div
          onClick={closeDetail}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
            backdropFilter: "blur(5px)",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: dashboardColors.cardBackground,
              padding: "32px",
              borderRadius: "16px",
              width: "100%",
              maxWidth: "800px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
              display: "flex",
              flexDirection: "column",
              gap: "20px",
              position: "relative",
            }}
          >
            <h2 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#1f2937", marginBottom: "8px" }}>
              Sample <span style={{ color: dashboardColors.primary }}>#{detailId}</span> Details
            </h2>

            {loadingDetail ? (
              <div style={{ textAlign: "center", padding: "40px", color: dashboardColors.neutralText }}>
                Loading isolate details...
              </div>
            ) : detail ? (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", fontSize: "1rem" }}>
                  <div>
                    <p style={{ marginBottom: "8px" }}>
                      <b style={{ color: "#4b5563" }}>Ward:</b> {detail.isolate.ward || "-"}
                    </p>
                    <p style={{ marginBottom: "8px" }}>
                      <b style={{ color: "#4b5563" }}>Organism:</b> {detail.isolate.organism || "-"}
                    </p>
                  </div>
                  <div>
                    <p style={{ marginBottom: "8px" }}>
                      <b style={{ color: "#4b5563" }}>Specimen Type:</b> {detail.isolate.sample_type || "-"}
                    </p>
                    <p style={{ marginBottom: "8px" }}>
                      <b style={{ color: "#4b5563" }}>ESBL Status:</b>{" "}
                      {detail.isolate.esbl_label
                        ? <Pill text="Positive" variant="positive" />
                        : <Pill text="Negative" variant="negative" />
                      }
                    </p>
                  </div>
                </div>

                <h3 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#1f2937", marginTop: "16px", marginBottom: "8px" }}>
                  Antimicrobial Susceptibility Testing (AST)
                </h3>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ background: "#f8fafc" }}>
                        <th style={{ padding: "12px 16px", textAlign: "left", borderBottom: "1px solid #e5e7eb", color: "#6b7280" }}>Antibiotic</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", borderBottom: "1px solid #e5e7eb", color: "#6b7280" }}>S/I/R</th>
                        <th style={{ padding: "12px 16px", textAlign: "left", borderBottom: "1px solid #e5e7eb", color: "#6b7280" }}>MIC</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.ast.length > 0 ? (
                        detail.ast.map((a, index) => (
                          <tr key={a.antibiotic || index} style={{ borderBottom: "1px solid #f1f5f9" }}>
                            <td style={{ padding: "10px 16px", fontSize: "0.9375rem", fontWeight: 500 }}>{a.antibiotic}</td>
                            <td style={{ padding: "10px 16px", fontSize: "0.9375rem" }}>
                              <Pill
                                text={a.sir}
                                variant={a.sir === "R" ? "positive" : a.sir === "S" ? "negative" : "neutral"}
                              />
                            </td>
                            <td style={{ padding: "10px 16px", fontSize: "0.9375rem" }}>{a.mic || "-"}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={3} style={{ padding: "20px", textAlign: "center", color: "#6b7280" }}>No AST data available.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div style={{ textAlign: "center", padding: "40px", color: dashboardColors.danger }}>
                Failed to load isolate details.
              </div>
            )}

            <Button onClick={closeDetail} variant="primary" style={{ alignSelf: "flex-end", marginTop: "20px" }}>
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- api_esbl.js (included for completeness, assuming it's a separate file) ---
// You would keep this in a separate file named api_esbl.js

/*
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/esbl",
});

export const fetchESBLWardSummary = async () => {
  try {
    const response = await api.get("/ward_summary");
    return response.data;
  } catch (error) {
    console.error("API Error fetching ward summary:", error);
    throw error;
  }
};

export const fetchESBLAntibiogram = async () => {
  try {
    const response = await api.get("/antibiogram");
    return response.data;
  } catch (error) {
    console.error("API Error fetching antibiogram:", error);
    throw error;
  }
};


export const fetchESBLIsolates = async (page, size, ward) => {
  try {
    const response = await api.get("/isolates", { params: { page, page_size: size, ward } });
    return response.data;
  } catch (error) {
    console.error("API Error fetching isolates:", error);
    throw error;
  }
};

export const fetchESBLIsolate = async (id) => {
  try {
    const response = await api.get(`/isolate/${id}`);
    return response.data;
  } catch (error) {
    console.error(`API Error fetching isolate ${id}:`, error);
    throw error;
  }
};
*/