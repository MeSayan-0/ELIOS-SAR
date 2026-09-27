import net from "net";

import {
  processAIEvent
} from "./perceptionPipeline.js";

const AI_PORT = Number(
  process.env.AI_STREAM_PORT || 8766
);

export function startAIStreamReceiver(port = Number(process.env.AI_STREAM_PORT || 8766)) {
  const server = net.createServer((socket) => {
    console.log("[AI] Sender connected");

    let buffer = "";

    socket.setEncoding("utf8");

    socket.on("data", (chunk) => {
      buffer += chunk;

      const messages =
        buffer.split("\n");

      buffer =
        messages.pop() || "";

      for (const line of messages) {
        const trimmed = line.trim();

        if (!trimmed) {
          continue;
        }

        try {
          const message =
            JSON.parse(trimmed);

          processAIEvent(message);
        } catch (error) {
          console.error(
            "[AI] Invalid JSON:",
            error.message
          );
        }
      }
    });

    socket.on("close", () => {
      console.log(
        "[AI] Sender disconnected"
      );
    });

    socket.on("error", (error) => {
      console.error(
        "[AI] Socket error:",
        error.message
      );
    });
  });

  server.on("error", (error) => {
    console.error(
      "[AI] Server error:",
      error.message
    );
  });

  server.listen(
    port,
    "0.0.0.0",
    () => {
      console.log(
        `[AI] Receiver listening on TCP ${port}`
      );
    }
  );

  return server;
}
