import mongoose from "mongoose";

const MapSchema = new mongoose.Schema(
  {
    mapId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },

    mapType: {
      type: String,
      required: true,
      enum: ["global", "local"],
    },

    vehicleId: {
      type: String,
      default: null,
      index: true,
    },

    missionId: {
      type: String,
      default: null,
      index: true,
    },

    frameId: {
      type: String,
      required: true,
    },

    timestamp: {
      type: Date,
      required: true,
    },

    resolution: {
      type: Number,
      required: true,
    },

    width: {
      type: Number,
      required: true,
    },

    height: {
      type: Number,
      required: true,
    },

    origin: {
      x: {
        type: Number,
        required: true,
      },

      y: {
        type: Number,
        required: true,
      },

      z: {
        type: Number,
        default: 0,
      },

      yaw: {
        type: Number,
        default: 0,
      },
    },

    grid: {
      type: [Number],
      required: true,
    },

    metadata: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  {
    timestamps: true,
  }
);

export const Map =
  mongoose.models.Map ||
  mongoose.model("Map", MapSchema);
