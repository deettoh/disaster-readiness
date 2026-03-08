export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function getRoute(params) {

  const query = new URLSearchParams(params).toString();

  const res = await fetch(`${API_BASE_URL}/route?${query}`);

  if (!res.ok) {
    throw new Error("Route API error");
  }

  return res.json();
}