import "dotenv/config";

import http from "http";
import express from "express";
import cors from "cors";

import { connectDatabase } from "./config/database.js";

import vehicleRoutes from "./routes/vehicles.js";
import telemetryRoutes from "./routes/telemetry.js";
import commandRoutes from "./routes/commands.js";
import detectionRoutes from "./routes/detections.js";
import operationsRoutes from "./routes/operations.js";
import mapRoutes from "./routes/maps.js";
import systemEventRoutes from "./routes/systemEvents.js";

import { getStateSnapshot } from "./services/stateService.js";
import { startRosStatusGateway } from "./services/rosStatusGateway.js";
import { startRosCommandGateway } from "./services/rosCommandGateway.js";
import { createWebSocketServer } from "./websocket/server.js";
import { broadcast } from "./websocket/manager.js";
import { startVideoStreamReceiver } from "./services/videoStreamService.js";
import { startAIStreamReceiver } from "./services/aiStreamService.js";

const app = express();

app.use(
  cors({
    origin:
      process.env.CLIENT_ORIGIN ||
      "http://localhost:5173",
  })
);

app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
  });
});

app.get("/api/state", async (_req, res) => {
  try {
    const state = await getStateSnapshot();
    res.json(state);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.use(
  "/api/vehicles",
  vehicleRoutes
);

app.use(
  "/api/telemetry",
  telemetryRoutes
);

app.use(
  "/api/commands",
  commandRoutes
);

app.use(
  "/api/detections",
  detectionRoutes
);

app.use(
  "/api/operations",
  operationsRoutes
);

app.use(
  "/api/maps",
  mapRoutes
);

app.use(
  "/api/system-events",
  systemEventRoutes
);

const server =
  http.createServer(app);

createWebSocketServer(server);
startVideoStreamReceiver(broadcast);
startAIStreamReceiver(broadcast);

const port =
  Number(process.env.PORT || 8000);

async function startServer() {
  await connectDatabase();

  startRosStatusGateway();
  startRosCommandGateway();

  server.listen(
    port,
    "0.0.0.0",
    () => {
      console.log(
        `ELIOS-SAR MERN backend listening on port ${port}`
      );
    }
  );
}

startServer().catch(
  (error) => {
    console.error(
      "Failed to start ELIOS-SAR backend:",
      error
    );

    process.exit(1);
  }
);
