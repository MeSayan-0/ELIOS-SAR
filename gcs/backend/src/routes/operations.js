import express from "express";

import {
  ingestSensor,
  ingestHazard,
  ingestRiskEvent,
  ingestMission,
} from "../services/operationsService.js";

import { broadcast } from "../websocket/manager.js";
import { getStateSnapshot } from "../services/stateService.js";

const router = express.Router();

async function sendState(res, result) {
  broadcast({
    type: "state",
    state: await getStateSnapshot(),
  });

  return res.status(201).json({
    accepted: true,
    result,
  });
}

router.post(
  "/sensors",
  async (req, res) => {
    try {
      const result =
        await ingestSensor(req.body);

      return sendState(res, result);
    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

router.post(
  "/hazards",
  async (req, res) => {
    try {
      const result =
        await ingestHazard(req.body);

      return sendState(res, result);
    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

router.post(
  "/risk-events",
  async (req, res) => {
    try {
      const result =
        await ingestRiskEvent(req.body);

      return sendState(res, result);
    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

router.post(
  "/missions",
  async (req, res) => {
    try {
      const result =
        await ingestMission(req.body);

      return sendState(res, result);
    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

export default router;
