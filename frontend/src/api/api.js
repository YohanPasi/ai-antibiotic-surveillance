import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // FastAPI backend

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Example: Fetch all patients
export const getPatients = async () => {
  const response = await api.get("/patients");
  return response.data;
};

// Example: Create new patient
export const createPatient = async (data) => {
  const response = await api.post("/patients", data);
  return response.data;
};
