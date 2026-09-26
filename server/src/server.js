import "dotenv/config";

import http from "http";
import express from "express";
import cors from "cors";

import { connectDatabase } from "./config/database.js";
import vehicleRoutes from "./routes/vehicles.js";
import { createWebSocketServer } from "./websocket/server.js";

const app = express();

app.use(
  cors({
    origin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
  })
);

app.use(express.json());

app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
  });
});

app.use("/api/vehicles", vehicleRoutes);

const server = http.createServer(app);

createWebSocketServer(server);

const port = Number(process.env.PORT || 8000);

await connectDatabase();

server.listen(port, () => {
  console.log(`ELIOS-SAR GCS server listening on port ${port}`);
});
