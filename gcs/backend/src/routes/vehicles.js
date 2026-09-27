import express from "express";

import { Telemetry } from "../models/Telemetry.js";
import { Vehicle } from "../models/Vehicle.js";
import { getAllVehicles, getVehicle } from "../services/gcsState.js";
import { registerVehicle } from "../services/vehicleService.js";
import { broadcast } from "../websocket/manager.js";
import { getStateSnapshot } from "../services/stateService.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  try {
    const vehicles = getAllVehicles();
    return res.json({
      vehicles,
    });
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});

router.get("/:vehicleId", async (req, res) => {
  try {
    const memVehicle = getVehicle(req.params.vehicleId);
    if (memVehicle) {
      return res.json(memVehicle);
    }

    const vehicle = await Vehicle.findOne({
      vehicleId: req.params.vehicleId,
    }).lean();

    if (!vehicle) {
      return res.status(404).json({
        error: "Vehicle not found",
      });
    }

    return res.json(vehicle);
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});

router.get("/:vehicleId/telemetry", async (req, res) => {
  try {
    const memVehicle = getVehicle(req.params.vehicleId);
    if (memVehicle?.telemetry && Object.keys(memVehicle.telemetry).length > 0) {
      return res.json({
        vehicleId: req.params.vehicleId,
        telemetry: [
          {
            vehicleId: req.params.vehicleId,
            timestamp: memVehicle.lastSeen || new Date(),
            data: memVehicle.telemetry,
          },
        ],
      });
    }

    const telemetry = await Telemetry.find({
      vehicleId: req.params.vehicleId,
    })
      .sort({ timestamp: -1 })
      .limit(100)
      .lean();

    return res.json({
      vehicleId: req.params.vehicleId,
      telemetry,
    });
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});

router.post("/register", async (req, res) => {
  try {
    const vehicle = await registerVehicle(req.body);

    broadcast({
      type: "vehicle_registered",
      vehicle,
    });

    broadcast({
      type: "state",
      state: await getStateSnapshot(),
    });

    return res.status(201).json({
      accepted: true,
      vehicle,
    });
  } catch (error) {
    return res.status(400).json({
      accepted: false,
      error: error.message,
    });
  }
});

export default router;
