const API_BASE =
  import.meta.env.VITE_GCS_API_URL ??
  import.meta.env.VITE_API_URL ??
  "";

export async function getSystemEvents(limit = 100) {
  const response = await fetch(
    `${API_BASE}/api/system-events?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(
      `System events request failed: ${response.status}`
    );
  }

  return response.json();
}
