// api_nonfermenter.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/nonfermenter",
});

// Ward summary: /nonfermenter/ward-summary
export const fetchNF_WardSummary = async () => {
  const res = await api.get("/ward-summary");
  return res.data || [];
};

// Antibiogram: /nonfermenter/antibiogram
export const fetchNF_Antibiogram = async () => {
  const res = await api.get("/antibiogram");
  return res.data || [];
};

// Paginated isolates: /nonfermenter/isolates?page=&page_size=&ward=
export const fetchNF_Isolates = async (page = 1, pageSize = 20, ward) => {
  const params = { page, page_size: pageSize };
  if (ward) params.ward = ward;
  const res = await api.get("/isolates", { params });
  return res.data || { items: [], total: 0 };
};

// Isolate detail: /nonfermenter/isolate/{id}
export const fetchNF_IsolateDetail = async (id) => {
  const res = await api.get(`/isolate/${id}`);
  return res.data;
};
