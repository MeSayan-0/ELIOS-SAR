import mongoose from "mongoose";

const telemetrySchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    timestamp: {
      type: Date,
      required: true,
    },

    data: {
      type: mongoose.Schema.Types.Mixed,
      required: true,
    },
  },
  {
    versionKey: false,
  }
);

export const Telemetry = mongoose.model(
  "Telemetry",
  telemetrySchema
);
