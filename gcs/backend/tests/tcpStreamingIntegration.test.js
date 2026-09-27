import test from "node:test";
import assert from "node:assert/strict";
import net from "node:net";

import { encodeVideoPacket } from "../src/services/videoProtocol.js";
import { startVideoStreamReceiver } from "../src/services/videoStreamService.js";
import { startAIStreamReceiver } from "../src/services/aiStreamService.js";
import { getSynchronizationState } from "../src/services/frameSynchronizer.js";

test("end-to-end TCP streaming across video and AI sockets", async (t) => {
  // Use non-standard ports for testing to avoid collisions
  const TEST_VIDEO_PORT = 18765;
  const TEST_AI_PORT = 18766;

  process.env.VIDEO_STREAM_PORT = String(TEST_VIDEO_PORT);
  process.env.AI_STREAM_PORT = String(TEST_AI_PORT);

  const videoServer = startVideoStreamReceiver(TEST_VIDEO_PORT);
  const aiServer = startAIStreamReceiver(TEST_AI_PORT);

  t.after(() => {
    videoServer.close();
    aiServer.close();
  });

  // Wait for servers to listen
  await new Promise((resolve) => setTimeout(resolve, 100));

  // 1. Connect AI client and send AI JSON message
  const aiSocket = net.createConnection({ port: TEST_AI_PORT, host: "127.0.0.1" });
  await new Promise((resolve, reject) => {
    aiSocket.on("connect", resolve);
    aiSocket.on("error", reject);
  });

  const aiMessage = {
    type: "AI_FRAME",
    source: "DRONE-01",
    frame_id: 888,
    timestamp: new Date().toISOString(),
    inference_time_ms: 220.0,
    inference_fps: 4.5,
    detections: [
      {
        id: "det-888-1",
        label: "person",
        confidence: 0.96,
        bbox: { x1: 50, y1: 100, x2: 250, y2: 400 },
        track_id: 1,
        severity: "high"
      }
    ],
    risk: {
      level: "HIGH",
      score: 88,
      reasons: ["person_found_in_hazard_sector"]
    }
  };

  aiSocket.write(JSON.stringify(aiMessage) + "\n");

  // 2. Connect Video client and send binary ELIO video packet
  const videoSocket = net.createConnection({ port: TEST_VIDEO_PORT, host: "127.0.0.1" });
  await new Promise((resolve, reject) => {
    videoSocket.on("connect", resolve);
    videoSocket.on("error", reject);
  });

  const dummyJpeg = Buffer.from([0xff, 0xd8, 0x11, 0x22, 0xff, 0xd9]);
  const videoPacket = encodeVideoPacket({
    frame_id: 888,
    timestamp_ms: Date.now(),
    jpeg: dummyJpeg
  });

  videoSocket.write(videoPacket);

  // Allow short moment for packet processing
  await new Promise((resolve) => setTimeout(resolve, 200));

  aiSocket.end();
  videoSocket.end();

  const syncState = getSynchronizationState();
  assert.ok(syncState.videos >= 1, "Expected video frames registered");
  assert.ok(syncState.ai_sources >= 1, "Expected AI events registered");
});
