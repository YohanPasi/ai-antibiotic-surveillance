import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

export async function registerUser(data) {
  const res = await api.post("/auth/register", data);
  return res.data;
}

export async function loginUser(username, password) {
  const res = await api.post("/auth/login", { username, password });
  return res.data;
}

export async function verifyToken(token) {
  try {
    const res = await api.get("/auth/verify", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch {
    return null;
  }
}
