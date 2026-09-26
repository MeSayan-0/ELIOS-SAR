import mongoose from "mongoose";

const commandSchema = new mongoose.Schema(
  {
    commandId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },

    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    vehicleType: {
      type: String,
      required: true,
      enum: ["drone", "rover"],
    },

    command: {
      type: String,
      required: true,
    },

    status: {
      type: String,
      required: true,
      enum: [
        "CREATED",
        "SENT",
        "ACCEPTED",
        "EXECUTING",
        "COMPLETED",
        "REJECTED",
        "FAILED",
      ],
      default: "CREATED",
    },

    source: {
      type: String,
      required: true,
      default: "GCS",
    },

    reason: {
      type: String,
      default: null,
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed,
      default: undefined,
    },

    createdAt: {
      type: Date,
      required: true,
    },

    updatedAt: {
      type: Date,
      required: true,
    },
  },
  {
    versionKey: false,
  }
);

export const Command = mongoose.model(
  "Command",
  commandSchema
);
