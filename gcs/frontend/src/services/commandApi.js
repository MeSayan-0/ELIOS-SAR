const API_BASE =
  import.meta.env.VITE_GCS_API_URL ||
  import.meta.env.VITE_API_URL ||
  `http://${window.location.hostname}:8000`;

async function request(
  path,
  options = {}
) {
  const response =
    await fetch(
      `${API_BASE}${path}`,
      {
        headers: {
          "Content-Type":
            "application/json",
          ...(options.headers || {}),
        },
        ...options,
      }
    );

  const data =
    await response.json();

  if (!response.ok) {
    throw new Error(
      data.error ||
      "GCS request failed"
    );
  }

  return data;
}

export async function getControlAuthority() {
  return request(
    "/api/commands/authority"
  );
}

export async function enableControl() {
  return request(
    "/api/commands/authority/enable",
    {
      method: "POST",
    }
  );
}

export async function disableControl() {
  return request(
    "/api/commands/authority/disable",
    {
      method: "POST",
    }
  );
}

export async function sendCommand({
  vehicleId,
  command,
  metadata = {},
}) {
  return request(
    "/api/commands",
    {
      method: "POST",
      body: JSON.stringify({
        vehicleId,
        command,
        metadata,
      }),
    }
  );
}

export async function getCommandLog() {
  return request(
    "/api/commands?limit=100"
  );
}

export async function emergencyStop(
  vehicleIds = []
) {
  return Promise.all(
    vehicleIds.map(
      (vehicleId) =>
        sendCommand({
          vehicleId,
          command: "ABORT",
          metadata: {
            emergency: true,
          },
        })
    )
  );
}
