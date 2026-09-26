import express from "express";

import { ingestDetection } from "../services/detectionService.js";
import { broadcast } from "../websocket/manager.js";
import { getStateSnapshot } from "../services/stateService.js";

const router = express.Router();

router.post("/", async (req, res) => {
  try {
    const detection = await ingestDetection(req.body);

    broadcast({
      type: "detection",
      detection,
    });

    broadcast({
      type: "state",
      state: await getStateSnapshot(),
    });

    return res.status(201).json({
      accepted: true,
      detection,
    });
  } catch (error) {
    return res.status(400).json({
      accepted: false,
      error: error.message,
    });
  }
});

export default router;
