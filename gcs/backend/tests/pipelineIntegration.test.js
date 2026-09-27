import test from "node:test";
import assert from "node:assert/strict";

import {
  encodeVideoPacket
} from "../src/services/videoProtocol.js";

import {
  processVideoFrame,
  processAIEvent
} from "../src/services/perceptionPipeline.js";

import {
  getSynchronizationState
} from "../src/services/frameSynchronizer.js";

test("perception pipeline synchronizes matching video and AI frames by frame_id", () => {
  const dummyJpeg = Buffer.from([0xff, 0xd8, 0x01, 0x02, 0xff, 0xd9]);
  const image = `data:image/jpeg;base64,${dummyJpeg.toString("base64")}`;
  const timestamp = new Date().toISOString();

  // 1. Process Video Frame (frame_id = 42)
  const videoResult = processVideoFrame({
    source: "drone-rgb",
    image,
    timestamp,
    timestamp_ms: 1758256200000,
    frame_id: 42
  });

  // Since no AI event with frame_id 42 exists yet, synchronized should be null or not synchronized
  assert.equal(videoResult, null);

  // 2. Process AI Event with matching frame_id 42
  const aiResult = processAIEvent({
    source: "drone-rgb",
    frame_id: 42,
    timestamp,
    inference_time_ms: 45.2,
    inference_fps: 22.1,
    detections: [
      {
        label: "person",
        confidence: 0.95,
        bbox: { x1: 10, y1: 20, x2: 100, y2: 200 }
      }
    ]
  });

  assert.ok(aiResult);
  assert.equal(aiResult.synchronized, true);
  assert.equal(aiResult.frame_id, 42);
  assert.equal(aiResult.detections.length, 1);
  assert.equal(aiResult.detections[0].label, "person");
  assert.equal(aiResult.detections[0].confidence, 0.95);

  const state = getSynchronizationState();
  assert.ok(state.videos >= 1);
  assert.ok(state.ai_sources >= 1);
});

test("perception pipeline handles unmatching frame_id gracefully", () => {
  const dummyJpeg = Buffer.from([0xff, 0xd8, 0x01, 0x02, 0xff, 0xd9]);
  const image = `data:image/jpeg;base64,${dummyJpeg.toString("base64")}`;

  processVideoFrame({
    source: "drone-rgb",
    image,
    timestamp: new Date().toISOString(),
    timestamp_ms: 1000,
    frame_id: 101
  });

  const aiResult = processAIEvent({
    source: "drone-rgb",
    frame_id: 999, // Different ID
    timestamp: new Date().toISOString(),
    detections: []
  });

  assert.ok(aiResult);
  assert.equal(aiResult.synchronized, false);
});

test("perception pipeline synchronizes cross-source identities (drone-rgb vs DRONE-01) and propagates risk", () => {
  const dummyJpeg = Buffer.from([0xff, 0xd8, 0x01, 0x02, 0xff, 0xd9]);
  const image = `data:image/jpeg;base64,${dummyJpeg.toString("base64")}`;
  const timestamp = "2026-09-19T10:30:15.123Z";

  // Video comes in as "drone-rgb"
  processVideoFrame({
    source: "drone-rgb",
    image,
    timestamp,
    timestamp_ms: 1758256200000,
    frame_id: 200
  });

  // AI comes in as "DRONE-01" with risk assessment
  const aiResult = processAIEvent({
    type: "AI_FRAME",
    source: "DRONE-01",
    frame_id: 200,
    timestamp,
    inference_time_ms: 245.5,
    inference_fps: 4.08,
    detections: [
      {
        id: "det-001",
        label: "person",
        confidence: 0.94,
        bbox: { x1: 120, y1: 80, x2: 340, y2: 420 },
        track_id: null,
        severity: "high"
      }
    ],
    risk: {
      level: "HIGH",
      score: 82,
      reasons: ["person_detected", "hazardous_gas"]
    }
  });

  assert.ok(aiResult);
  assert.equal(aiResult.synchronized, true);
  assert.equal(aiResult.frame_id, 200);
  assert.equal(aiResult.source, "DRONE-01");
  assert.equal(aiResult.vehicle_id, "DRONE-01");
  assert.equal(aiResult.stream_id, "drone-01-rgb");
  assert.equal(aiResult.detections.length, 1);
  assert.equal(aiResult.detections[0].label, "person");
  assert.equal(aiResult.detections[0].confidence, 0.94);
  assert.equal(aiResult.detections[0].severity, "high");

  // Verify Risk Propagation
  assert.ok(aiResult.risk);
  assert.equal(aiResult.risk.level, "HIGH");
  assert.equal(aiResult.risk.score, 82);
  assert.deepEqual(aiResult.risk.reasons, ["person_detected", "hazardous_gas"]);
});

test("perception pipeline synchronizes when video arrives after AI with matching frame_id", () => {
  const dummyJpeg = Buffer.from([0xff, 0xd8, 0xaa, 0xbb, 0xff, 0xd9]);
  const image = `data:image/jpeg;base64,${dummyJpeg.toString("base64")}`;
  const timestamp = "2026-09-19T10:30:20.000Z";

  // 1. AI arrives first
  const aiEventResult = processAIEvent({
    type: "AI_FRAME",
    source: "DRONE-01",
    frame_id: 300,
    timestamp,
    inference_time_ms: 180.0,
    inference_fps: 5.5,
    detections: [
      {
        label: "person",
        confidence: 0.98,
        bbox: [100, 150, 300, 450]
      }
    ],
    risk: "CRITICAL"
  });

  // Since video frame 300 hasn't arrived yet, aiEventResult should not yet match frame 300 video
  // (or will report false because previous video in map is frame 200)
  assert.equal(aiEventResult.synchronized, false);

  // 2. Video arrives second with matching frame_id 300
  const videoResult = processVideoFrame({
    source: "drone-rgb",
    image,
    timestamp,
    timestamp_ms: 1758256300000,
    frame_id: 300
  });

  // Video registration should trigger synchronization with matching AI event 300!
  assert.ok(videoResult);
  assert.equal(videoResult.synchronized, true);
  assert.equal(videoResult.frame_id, 300);
  assert.equal(videoResult.detections.length, 1);
  assert.equal(videoResult.risk.level, "CRITICAL");
  assert.equal(videoResult.risk.score, 100);
});

test("riskService calculates risk correctly and pipeline enriches AI event with risk", () => {
  const aiResult = processAIEvent({
    source: "DRONE-01",
    frame_id: 999,
    timestamp: new Date().toISOString(),
    detections: [
      { label: "person", confidence: 0.9, severity: "high" },
      { label: "fire", confidence: 0.85, severity: "high" }
    ]
  });

  assert.ok(aiResult);
  assert.ok(aiResult.risk);
  assert.equal(aiResult.risk.score, 70);
  assert.equal(aiResult.risk.level, "HIGH");
  assert.match(aiResult.risk.reason, /PERSON DETECTED/);
  assert.match(aiResult.risk.reason, /FIRE DETECTED/);
});
