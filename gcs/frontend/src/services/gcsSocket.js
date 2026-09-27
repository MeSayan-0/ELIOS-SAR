const WS_URL =
  import.meta.env.VITE_GCS_WS_URL ||
  (typeof window !== "undefined" && window.location?.host
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`
    : "ws://localhost:8000/ws");

let socket = null;
let disconnectTimer = null;
let reconnectTimer = null;
let isIntentionalClose = false;

const listeners = new Set();

function notify(event) {
  for (const listener of listeners) {
    try {
      listener(event);
    } catch (error) {
      console.error("GCS listener error:", error);
    }
  }
}

export function connectGCS() {
  if (disconnectTimer) {
    clearTimeout(disconnectTimer);
    disconnectTimer = null;
  }

  if (
    socket &&
    (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    )
  ) {
    return socket;
  }

  isIntentionalClose = false;

  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      notify({
        type: "connection",
        connected: true,
      });
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        notify({
          type: "state",
          state: message,
        });
      } catch (error) {
        notify({
          type: "error",
          error,
        });
      }
    };

    socket.onerror = (error) => {
      if (!isIntentionalClose) {
        notify({
          type: "error",
          error,
        });
      }
    };

    socket.onclose = () => {
      const wasIntentional = isIntentionalClose;
      socket = null;

      notify({
        type: "connection",
        connected: false,
      });

      if (!wasIntentional && listeners.size > 0 && !reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          if (listeners.size > 0) {
            connectGCS();
          }
        }, 2000);
      }
    };
  } catch (err) {
    console.error("Failed to initialize GCS WebSocket:", err);
  }

  return socket;
}

export function disconnectGCS() {
  if (disconnectTimer) {
    clearTimeout(disconnectTimer);
  }

  disconnectTimer = setTimeout(() => {
    disconnectTimer = null;

    if (listeners.size > 0) {
      return;
    }

    if (socket) {
      isIntentionalClose = true;
      const s = socket;
      socket = null;

      s.onerror = null;
      s.onmessage = null;

      if (s.readyState === WebSocket.OPEN) {
        s.close();
      } else if (s.readyState === WebSocket.CONNECTING) {
        s.onopen = () => {
          try {
            s.close();
          } catch (_) {}
        };
      }
    }
  }, 250);
}

export function subscribeGCS(listener) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

export function sendGCSCommand(command) {
  if (
    !socket ||
    socket.readyState !== WebSocket.OPEN
  ) {
    throw new Error(
      "GCS WebSocket is not connected"
    );
  }

  socket.send(
    JSON.stringify(command)
  );
}
