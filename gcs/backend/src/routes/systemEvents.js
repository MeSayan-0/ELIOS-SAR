import express from "express";
import { getSystemEvents } from "../services/systemEventService.js";

const router = express.Router();

router.get("/", async (req, res) => {
  try {
    const limit = Math.min(
      Number(req.query.limit) || 100,
      500
    );

    const events = await getSystemEvents(limit);

    return res.json({
      events,
    });
  } catch (error) {
    return res.status(500).json({
      events: [],
      error: error.message,
    });
  }
});

export default router;
