import mongoose from "mongoose";

const detectionSchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    detectionId: {
      type: String,
      required: true,
      unique: true,
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

export const Detection = mongoose.model(
  "Detection",
  detectionSchema
);
