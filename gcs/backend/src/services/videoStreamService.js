import net from "net";

import {
  processVideoFrame
} from "./perceptionPipeline.js";

import {
  VIDEO_HEADER_SIZE,
  MAX_VIDEO_PAYLOAD_SIZE,
  decodeVideoHeader
} from "./videoProtocol.js";

const VIDEO_PORT = Number(
  process.env.VIDEO_STREAM_PORT || 8765
);

export function startVideoStreamReceiver(port = Number(process.env.VIDEO_STREAM_PORT || 8765)) {
  const server = net.createServer((socket) => {
    console.log("[VIDEO] Sender connected");

    let buffer = Buffer.alloc(0);

    function processBuffer() {
      while (true) {
        if (buffer.length < VIDEO_HEADER_SIZE) {
          return;
        }

        let header;

        try {
          header = decodeVideoHeader(buffer);
        } catch (error) {
          console.error(
            "[VIDEO] Protocol error:",
            error.message
          );

          socket.destroy();
          return;
        }

        const packetSize =
          VIDEO_HEADER_SIZE +
          header.payload_length;

        if (buffer.length < packetSize) {
          return;
        }

        const jpeg = buffer.subarray(
          VIDEO_HEADER_SIZE,
          packetSize
        );

        buffer = buffer.subarray(packetSize);

        const image =
          `data:image/jpeg;base64,${jpeg.toString("base64")}`;

        const timestamp =
          new Date(header.timestamp_ms).toISOString();

        processVideoFrame({
          source: "drone-rgb",
          image,
          timestamp,
          timestamp_ms: header.timestamp_ms,
          frame_id: header.frame_id
        });
      }
    }

    socket.on("data", (chunk) => {
      buffer = Buffer.concat([
        buffer,
        chunk
      ]);

      if (
        buffer.length >
        MAX_VIDEO_PAYLOAD_SIZE +
        VIDEO_HEADER_SIZE
      ) {
        console.error(
          "[VIDEO] Receive buffer exceeded safe limit"
        );

        socket.destroy();
        return;
      }

      try {
        processBuffer();
      } catch (error) {
        console.error(
          "[VIDEO] Processing error:",
          error.message
        );

        socket.destroy();
      }
    });

    socket.on("close", () => {
      console.log("[VIDEO] Sender disconnected");
    });

    socket.on("error", (error) => {
      console.error(
        "[VIDEO] Socket error:",
        error.message
      );
    });
  });

  server.on("error", (error) => {
    console.error(
      "[VIDEO] Server error:",
      error.message
    );
  });

  server.listen(
    port,
    "0.0.0.0",
    () => {
      console.log(
        `[VIDEO] Receiver listening on TCP ${port}`
      );
    }
  );

  return server;
}
