const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function fetchIsolates(page = 1, pageSize = 20, ward) {
  const url = new URL(`${BASE}/mrsa/isolates`);
  url.searchParams.set("page", String(page));
  url.searchParams.set("page_size", String(pageSize));
  if (ward) url.searchParams.set("ward", ward);
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to load isolates");
  return res.json();
}

export async function fetchWardSummary() {
  const res = await fetch(`${BASE}/mrsa/summary/ward`);
  if (!res.ok) throw new Error("Failed to load ward summary");
  return res.json();
}

export async function fetchAntibiogram() {
  const res = await fetch(`${BASE}/mrsa/summary/antibiogram`);
  if (!res.ok) throw new Error("Failed to load antibiogram");
  return res.json();
}

export async function fetchIsolate(sampleId) {
  const res = await fetch(`${BASE}/mrsa/isolate/${sampleId}`);
  if (!res.ok) throw new Error("Failed to load isolate");
  return res.json();
}
