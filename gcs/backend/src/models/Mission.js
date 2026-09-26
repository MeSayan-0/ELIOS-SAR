import mongoose from "mongoose";

const missionSchema = new mongoose.Schema(
  {
    missionId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },

    vehicleId: {
      type: String,
      required: false,
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

export const Mission = mongoose.model(
  "Mission",
  missionSchema
);
