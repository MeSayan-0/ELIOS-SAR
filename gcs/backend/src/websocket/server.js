import { WebSocketServer } from "ws";
import {
  addClient,
  removeClient,
} from "./manager.js";
import { getStateSnapshot } from "../services/stateService.js";

export function createWebSocketServer(server) {
  const wss = new WebSocketServer({
    server,
    path: "/ws",
  });

  wss.on("connection", async (ws) => {
    addClient(ws);

    try {
      const state = await getStateSnapshot();
      ws.send(JSON.stringify(state));
    } catch (err) {
      console.warn("Could not send initial state to client:", err.message);
    }

    ws.on("close", () => {
      removeClient(ws);
    });

    ws.on("error", () => {
      removeClient(ws);
    });
  });

  return wss;
}
