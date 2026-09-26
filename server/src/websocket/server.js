import { WebSocketServer } from "ws";
import {
  addClient,
  removeClient,
} from "./manager.js";

export function createWebSocketServer(server) {
  const wss = new WebSocketServer({
    server,
    path: "/ws",
  });

  wss.on("connection", (ws) => {
    addClient(ws);

    ws.on("close", () => {
      removeClient(ws);
    });

    ws.on("error", () => {
      removeClient(ws);
    });
  });

  return wss;
}
