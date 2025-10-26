import axios from "axios";

// Prefer env var if present; fallback to localhost
const API_BASE_URL = import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  // If you need cookies later, add: withCredentials: true
});

// GET /patients -> list
export const getPatients = async () => {
  try {
    const { data } = await api.get("/patients");
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("getPatients failed:", err?.response?.data || err.message);
    return []; // keep UI stable
  }
};

// POST /patients -> created record
export const createPatient = async (payload) => {
  const body = {
    age: Number(payload.age),
    sex: String(payload.sex || ""),
    ward: String(payload.ward || ""),
    diagnosis: payload.diagnosis ?? null,
  };
  const { data } = await api.post("/patients", body);
  return data;
};
