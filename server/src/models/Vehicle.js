import mongoose from "mongoose";

const vehicleSchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      unique: true,
      trim: true,
    },

    vehicleType: {
      type: String,
      required: true,
      enum: ["drone", "rover"],
    },

    connected: {
      type: Boolean,
      required: true,
    },

    lastSeen: {
      type: Date,
      required: true,
    },

    telemetry: {
      type: mongoose.Schema.Types.Mixed,
      default: undefined,
    },

    sensors: {
      type: mongoose.Schema.Types.Mixed,
      default: undefined,
    },
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

export const Vehicle = mongoose.model("Vehicle", vehicleSchema);
