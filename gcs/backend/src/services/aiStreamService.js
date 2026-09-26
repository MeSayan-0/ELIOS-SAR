import { WebSocketServer } from "ws";

const AI_PORT = Number(process.env.AI_WS_PORT || 8766);

export function startAIStreamReceiver(broadcast) {
  const wss = new WebSocketServer({
    host: "0.0.0.0",
    port: AI_PORT,
  });

  console.log(
    `[AI] WebSocket receiver listening on 0.0.0.0:${AI_PORT}`
  );

  wss.on("connection", (ws, request) => {
    const remoteAddress = request.socket.remoteAddress;

    console.log(
      `[AI] AI client connected from ${remoteAddress}`
    );

    ws.on("message", (data) => {
      try {
        const text = data.toString();
        const message = JSON.parse(text);

        broadcast({
          type: "ai_event",
          data: message,
        });
      } catch (error) {
        console.error(
          "[AI] Invalid JSON message:",
          error
        );
      }
    });

    ws.on("close", () => {
      console.log(
        `[AI] AI client disconnected from ${remoteAddress}`
      );
    });

    ws.on("error", (error) => {
      console.error(
        "[AI] WebSocket error:",
        error
      );
    });
  });

  wss.on("error", (error) => {
    console.error(
      "[AI] WebSocket server error:",
      error
    );
  });

  return wss;
}
