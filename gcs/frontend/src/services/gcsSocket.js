const WS_URL =
  import.meta.env.VITE_GCS_WS_URL ||
  `ws://${window.location.hostname}:8000/ws`;

let socket = null;

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
  if (
    socket &&
    (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    )
  ) {
    return socket;
  }

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
    notify({
      type: "error",
      error,
    });
  };

  socket.onclose = () => {
    notify({
      type: "connection",
      connected: false,
    });

    socket = null;
  };

  return socket;
}

export function disconnectGCS() {
  if (socket) {
    socket.close();
    socket = null;
  }
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
