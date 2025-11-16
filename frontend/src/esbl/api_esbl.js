import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/esbl",
});

export const fetchESBLWardSummary = async () =>
  (await api.get("/ward_summary")).data;

export const fetchESBLAntibiogram = async () =>
  (await api.get("/antibiogram")).data;

export const fetchESBLIsolates = async (page, size, ward) =>
  (await api.get("/isolates", { params: { page, page_size: size, ward } })).data;

export const fetchESBLIsolate = async (id) =>
  (await api.get(`/isolate/${id}`)).data;
