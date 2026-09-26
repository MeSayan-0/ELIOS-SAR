import mongoose from "mongoose";

const riskEventSchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    riskId: {
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

export const RiskEvent = mongoose.model(
  "RiskEvent",
  riskEventSchema
);
