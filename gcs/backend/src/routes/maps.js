import express from "express";

import {
  ingestMap,
  getMap,
  getLatestMap,
  getMaps,
} from "../services/mapService.js";

import {
  broadcast,
} from "../websocket/manager.js";

const router = express.Router();


/*
 * GET /api/maps
 *
 * Optional query parameters:
 *
 * ?mapType=global
 * ?mapType=local
 * ?vehicleId=DRONE-01
 * ?missionId=MISSION-A
 */

router.get("/", async (req, res) => {
  try {
    const maps = await getMaps({
      mapType: req.query.mapType,
      vehicleId: req.query.vehicleId,
      missionId: req.query.missionId,
    });

    return res.json({
      maps,
    });
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});


/*
 * GET /api/maps/latest
 */

router.get("/latest", async (req, res) => {
  try {
    if (!req.query.mapType) {
      return res.status(400).json({
        error: "mapType is required",
      });
    }

    const map = await getLatestMap({
      mapType: req.query.mapType,
      vehicleId: req.query.vehicleId,
      missionId: req.query.missionId,
    });

    if (!map) {
      return res.status(404).json({
        error: "Map not found",
      });
    }

    return res.json(map);
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});


/*
 * GET /api/maps/:mapId
 */

router.get("/:mapId", async (req, res) => {
  try {
    const map = await getMap(
      req.params.mapId
    );

    if (!map) {
      return res.status(404).json({
        error: "Map not found",
      });
    }

    return res.json(map);
  } catch (error) {
    return res.status(500).json({
      error: error.message,
    });
  }
});


/*
 * POST /api/maps
 *
 * External producers:
 *
 * ROS 2
 * SLAM
 * LiDAR bridge
 * simulator
 * future physical system
 */

router.post("/", async (req, res) => {
  try {
    const map = await ingestMap(
      req.body
    );

    broadcast({
      type: "map",
      map,
    });

    return res.status(202).json({
      accepted: true,
      map,
    });
  } catch (error) {
    return res.status(400).json({
      accepted: false,
      error: error.message,
    });
  }
});


export default router;
