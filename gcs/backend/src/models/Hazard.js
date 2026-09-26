import mongoose from "mongoose";

const hazardSchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    hazardId: {
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

export const Hazard = mongoose.model(
  "Hazard",
  hazardSchema
);
