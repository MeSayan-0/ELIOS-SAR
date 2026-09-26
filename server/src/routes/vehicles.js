import express from "express";
import { Vehicle } from "../models/Vehicle.js";

const router = express.Router();

router.get("/", async (_req, res) => {
  try {
    const vehicles = await Vehicle.find()
      .sort({ vehicleId: 1 })
      .lean();

    res.json({
      vehicles,
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
    });
  }
});

router.get("/:vehicleId", async (req, res) => {
  try {
    const vehicle = await Vehicle.findOne({
      vehicleId: req.params.vehicleId,
    }).lean();

    if (!vehicle) {
      return res.status(404).json({
        error: "Vehicle not found",
      });
    }

    res.json(vehicle);
  } catch (error) {
    res.status(500).json({
      error: error.message,
    });
  }
});

export default router;
