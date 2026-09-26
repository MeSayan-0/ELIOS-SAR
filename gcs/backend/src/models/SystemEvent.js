import mongoose from "mongoose";

const systemEventSchema = new mongoose.Schema(
  {
    timestamp: {
      type: Date,
      required: true,
      default: Date.now,
      index: true,
    },

    level: {
      type: String,
      enum: [
        "INFO",
        "WARN",
        "ERROR",
        "CRITICAL",
      ],
      default: "INFO",
    },

    source: {
      type: String,
      required: true,
    },

    eventType: {
      type: String,
      required: true,
    },

    vehicleId: {
      type: String,
      default: null,
    },

    missionId: {
      type: String,
      default: null,
    },

    message: {
      type: String,
      required: true,
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  {
    versionKey: false,
  }
);

export const SystemEvent = mongoose.model(
  "SystemEvent",
  systemEventSchema
);
