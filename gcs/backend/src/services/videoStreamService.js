import { WebSocketServer } from "ws";

const VIDEO_PORT = Number(process.env.VIDEO_WS_PORT || 8765);

export function startVideoStreamReceiver(broadcast) {
  const wss = new WebSocketServer({
    host: "0.0.0.0",
    port: VIDEO_PORT,
  });

  console.log(
    `[VIDEO] WebSocket receiver listening on 0.0.0.0:${VIDEO_PORT}`
  );

  wss.on("connection", (ws, request) => {
    const remoteAddress = request.socket.remoteAddress;

    console.log(
      `[VIDEO] AI client connected from ${remoteAddress}`
    );

    ws.on("message", (data, isBinary) => {
      if (!isBinary) {
        console.warn(
          "[VIDEO] Received non-binary message; expected JPEG bytes"
        );
        return;
      }

      try {
        const buffer = Buffer.from(data);

        if (buffer.length === 0) {
          console.warn("[VIDEO] Received empty frame");
          return;
        }

        const image =
          `data:image/jpeg;base64,${buffer.toString("base64")}`;

        broadcast({
          type: "video_frame",
          source: "drone-rgb",
          image,
        });
      } catch (error) {
        console.error(
          "[VIDEO] Failed to process video frame:",
          error
        );
      }
    });

    ws.on("close", () => {
      console.log(
        `[VIDEO] AI client disconnected from ${remoteAddress}`
      );
    });

    ws.on("error", (error) => {
      console.error(
        "[VIDEO] WebSocket error:",
        error
      );
    });
  });

  wss.on("error", (error) => {
    console.error(
      "[VIDEO] WebSocket server error:",
      error
    );
  });

  return wss;
}
