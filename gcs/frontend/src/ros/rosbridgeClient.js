class RosbridgeClient {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.connected = false;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket) {
      return;
    }

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.connected = true;
        this.emit("connection", {
          connected: true,
        });
      };

      this.socket.onclose = () => {
        this.connected = false;
        this.emit("connection", {
          connected: false,
        });

        this.socket = null;
      };

      this.socket.onerror = (error) => {
        this.emit("error", error);
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.op === "publish") {
            this.emit(message.topic, message.msg);
          }
        } catch (error) {
          console.error("ROS message parse error:", error);
        }
      };
    } catch (err) {
      this.connected = false;
      this.emit("error", err);
    }
  }

  subscribe(topic, type) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.warn("ROS socket is not connected");
      return;
    }

    this.socket.send(
      JSON.stringify({
        op: "subscribe",
        topic,
        type,
      })
    );
  }

  publish(topic, type, msg) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.warn("ROS socket is not connected");
      return;
    }

    this.socket.send(
      JSON.stringify({
        op: "publish",
        topic,
        type,
        msg,
      })
    );
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }

    this.listeners.get(event).add(callback);

    return () => {
      this.listeners.get(event)?.delete(callback);
    };
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event);

    if (!callbacks) {
      return;
    }

    callbacks.forEach((callback) => {
      callback(data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.connected = false;
  }
}

const rosbridgeUrl =
  import.meta.env.VITE_ROSBRIDGE_URL || "ws://localhost:9090";

export const rosbridgeClient = new RosbridgeClient(rosbridgeUrl);
