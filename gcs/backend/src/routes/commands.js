import express from "express";

import {
  createCommand,
  updateCommandStatus,
  getRecentCommands,
  getVehicleCommands,
} from "../services/commandService.js";

import {
  enableControlAuthority,
  disableControlAuthority,
  getControlAuthority,
  requireControlAuthority,
} from "../services/controlAuthority.js";

import {
  publishDroneCommand,
  publishRoverCommand,
} from "../services/rosCommandGateway.js";

import {
  broadcast,
} from "../websocket/manager.js";

const router = express.Router();

/* --------------------------------------------------------- */
/* CONTROL AUTHORITY                                         */
/* --------------------------------------------------------- */

router.get(
  "/authority",
  (_req, res) => {
    return res.json({
      authority:
        getControlAuthority(),
    });
  }
);

router.post(
  "/authority/enable",
  (_req, res) => {
    const authority =
      enableControlAuthority();

    broadcast({
      type: "control_authority",
      authority,
    });

    return res.json({
      accepted: true,
      authority,
    });
  }
);

router.post(
  "/authority/disable",
  (_req, res) => {
    const authority =
      disableControlAuthority();

    broadcast({
      type: "control_authority",
      authority,
    });

    return res.json({
      accepted: true,
      authority,
    });
  }
);

/* --------------------------------------------------------- */
/* CREATE COMMAND                                             */
/* --------------------------------------------------------- */

router.post(
  "/",
  async (req, res) => {
    try {
      requireControlAuthority();

      const {
        vehicleId,
        command,
        metadata,
      } = req.body;

      const result =
        await createCommand({
          vehicleId,
          command,
          metadata,
        });

      let commandRecord =
        result.command;

      if (
        result.vehicle.vehicleType === "drone"
      ) {
        try {
          publishDroneCommand({
            vehicleId:
              result.vehicle.vehicleId,

            command:
              result.command.command,

            commandId:
              result.command.commandId,
          });

          commandRecord =
            await updateCommandStatus(
              result.command.commandId,
              "SENT"
            );

        } catch (error) {
          commandRecord =
            await updateCommandStatus(
              result.command.commandId,
              "FAILED",
              error.message
            );

          return res.status(503).json({
            accepted: false,
            error:
              error.message,
            command:
              commandRecord,
          });
        }
      }

      if (
        result.vehicle.vehicleType === "rover"
      ) {
        const roverMotionCommands = new Set([
          "FORWARD",
          "BACK",
          "LEFT",
          "RIGHT",
          "STOP",
          "RETURN_TO_DOCK",
          "DOCK",
          "ABORT",
        ]);

        if (
          roverMotionCommands.has(
            result.command.command
          )
        ) {
          try {
            publishRoverCommand({
              vehicleId:
                result.vehicle.vehicleId,

              command:
                result.command.command,

              commandId:
                result.command.commandId,

              metadata:
                result.command.metadata,
            });

            commandRecord =
              await updateCommandStatus(
                result.command.commandId,
                "SENT"
              );

          } catch (error) {
            commandRecord =
              await updateCommandStatus(
                result.command.commandId,
                "FAILED",
                error.message
              );

            return res.status(503).json({
              accepted: false,
              error:
                error.message,
              command:
                commandRecord,
            });
          }
        }
      }

      broadcast({
        type: "command",
        command: commandRecord,
      });

      return res.status(202).json({
        accepted: true,
        command: commandRecord,
      });

    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

/* --------------------------------------------------------- */
/* COMMAND STATUS                                             */
/* --------------------------------------------------------- */

router.patch(
  "/:commandId/status",
  async (req, res) => {
    try {
      const {
        status,
        reason,
      } = req.body;

      const command =
        await updateCommandStatus(
          req.params.commandId,
          status,
          reason
        );

      broadcast({
        type: "command_status",
        command,
      });

      return res.json({
        accepted: true,
        command,
      });

    } catch (error) {
      return res.status(400).json({
        accepted: false,
        error: error.message,
      });
    }
  }
);

/* --------------------------------------------------------- */
/* COMMAND LOG                                                */
/* --------------------------------------------------------- */

router.get(
  "/",
  async (req, res) => {
    try {
      const limit =
        Number(req.query.limit || 100);

      const commands =
        await getRecentCommands(
          Math.min(limit, 500)
        );

      return res.json({
        commands,
      });

    } catch (error) {
      return res.status(500).json({
        error: error.message,
      });
    }
  }
);

router.get(
  "/vehicle/:vehicleId",
  async (req, res) => {
    try {
      const commands =
        await getVehicleCommands(
          req.params.vehicleId
        );

      return res.json({
        commands,
      });

    } catch (error) {
      return res.status(500).json({
        error: error.message,
      });
    }
  }
);

export default router;
