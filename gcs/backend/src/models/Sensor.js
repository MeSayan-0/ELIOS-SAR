import mongoose from "mongoose";

const sensorSchema = new mongoose.Schema(
  {
    vehicleId: {
      type: String,
      required: true,
      index: true,
    },

    sensorId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },

    sensorType: {
      type: String,
      required: true,
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

export const Sensor = mongoose.model(
  "Sensor",
  sensorSchema
);
