import test from "node:test";
import assert from "node:assert/strict";

import {
  encodeVideoPacket,
  decodeVideoHeader,
  VIDEO_HEADER_SIZE
} from "../src/services/videoProtocol.js";

test("video packet encodes frame metadata", () => {
  const jpeg = Buffer.from([
    0xff,
    0xd8,
    0x01,
    0x02,
    0xff,
    0xd9
  ]);

  const packet = encodeVideoPacket({
    frame_id: 123,
    timestamp_ms: 1758256200000,
    jpeg
  });

  assert.equal(
    packet.length,
    VIDEO_HEADER_SIZE + jpeg.length
  );

  const header =
    decodeVideoHeader(packet);

  assert.equal(
    header.frame_id,
    123
  );

  assert.equal(
    header.timestamp_ms,
    1758256200000
  );

  assert.equal(
    header.payload_length,
    jpeg.length
  );
});

test("video packet handles fragmented buffer", () => {
  const jpeg = Buffer.from([0xff, 0xd8, 0xaa, 0xbb, 0xff, 0xd9]);
  const packet = encodeVideoPacket({
    frame_id: 999,
    timestamp_ms: 1758256300000,
    jpeg
  });

  // Partial header should return null
  assert.equal(decodeVideoHeader(packet.subarray(0, 10)), null);

  // Full header should decode
  const header = decodeVideoHeader(packet);
  assert.equal(header.frame_id, 999);
});
