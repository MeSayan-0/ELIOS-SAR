import express from "express";

import {
  ingestTelemetry,
} from "../services/telemetryService.js";

import {
  broadcast,
} from "../websocket/manager.js";

import {
  getStateSnapshot,
} from "../services/stateService.js";

const router = express.Router();


router.post("/", async (req, res) => {
  try {
    const result =
      await ingestTelemetry(req.body);

    broadcast({
      type: "telemetry",
      telemetry: result.telemetry,
      vehicle: result.vehicle,
    });

    broadcast({
      type: "state",
      state: await getStateSnapshot(),
    });

    return res.status(202).json({
      accepted: true,
      telemetry: result.telemetry,
      vehicle: result.vehicle,
    });

  } catch (error) {
    return res.status(400).json({
      accepted: false,
      error: error.message,
    });
  }
});


router.get("/:vehicleId", async (req, res) => {
  try {
    const {
      Telemetry,
    } = await import(
      "../models/Telemetry.js"
    );

    const telemetry =
      await Telemetry.find({
        vehicleId:
          req.params.vehicleId,
      })
        .sort({
          timestamp: -1,
        })
        .limit(100)
        .lean();

    return res.json({
      vehicleId:
        req.params.vehicleId,
      telemetry,
    });

  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});


export default router;
