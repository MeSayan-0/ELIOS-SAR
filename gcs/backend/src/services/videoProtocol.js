const MAGIC = Buffer.from("ELIO");
const VERSION = 1;

export const VIDEO_HEADER_SIZE = 25;
export const MAX_VIDEO_PAYLOAD_SIZE = 5 * 1024 * 1024;

export function encodeVideoPacket({
  frame_id,
  timestamp_ms,
  jpeg
}) {
  if (!Number.isInteger(frame_id) || frame_id < 0) {
    throw new Error("Invalid frame_id");
  }

  if (!Number.isInteger(timestamp_ms) || timestamp_ms < 0) {
    throw new Error("Invalid timestamp_ms");
  }

  if (!Buffer.isBuffer(jpeg)) {
    throw new Error("JPEG payload must be a Buffer");
  }

  if (jpeg.length === 0) {
    throw new Error("JPEG payload is empty");
  }

  if (jpeg.length > MAX_VIDEO_PAYLOAD_SIZE) {
    throw new Error("JPEG payload exceeds maximum size");
  }

  const header = Buffer.alloc(VIDEO_HEADER_SIZE);

  MAGIC.copy(header, 0);

  header.writeUInt8(VERSION, 4);

  header.writeBigUInt64BE(
    BigInt(frame_id),
    5
  );

  header.writeBigUInt64BE(
    BigInt(timestamp_ms),
    13
  );

  header.writeUInt32BE(
    jpeg.length,
    21
  );

  return Buffer.concat([
    header,
    jpeg
  ]);
}

export function decodeVideoHeader(buffer) {
  if (buffer.length < VIDEO_HEADER_SIZE) {
    return null;
  }

  if (!buffer.subarray(0, 4).equals(MAGIC)) {
    throw new Error("Invalid video packet magic");
  }

  const version = buffer.readUInt8(4);

  if (version !== VERSION) {
    throw new Error(
      `Unsupported video protocol version: ${version}`
    );
  }

  const frame_id = Number(
    buffer.readBigUInt64BE(5)
  );

  const timestamp_ms = Number(
    buffer.readBigUInt64BE(13)
  );

  const payload_length =
    buffer.readUInt32BE(21);

  if (
    payload_length <= 0 ||
    payload_length > MAX_VIDEO_PAYLOAD_SIZE
  ) {
    throw new Error(
      `Invalid JPEG payload length: ${payload_length}`
    );
  }

  return {
    frame_id,
    timestamp_ms,
    payload_length
  };
}
