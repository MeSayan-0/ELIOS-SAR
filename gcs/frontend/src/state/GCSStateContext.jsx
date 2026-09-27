import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  connectGCS,
  disconnectGCS,
  subscribeGCS,
} from "../services/gcsSocket";

import {
  startRosSubscriptions,
} from "../ros/rosSubscriptions";

import {
  EMPTY_GCS_STATE,
  normalizeGCSState,
} from "./gcsState";

const GCSStateContext = createContext(null);

export function GCSStateProvider({ children }) {
  const [state, setState] =
    useState(EMPTY_GCS_STATE);

  const [connected, setConnected] =
    useState(false);

  const [selectedVehicleId, setSelectedVehicleId] =
    useState(null);

  // In-memory buffer to accumulate high-frequency ROS messages
  const stateRef = useRef(EMPTY_GCS_STATE);
  const hasPendingRosUpdatesRef = useRef(false);

  // 1. MERN backend WebSocket subscription
  useEffect(() => {
    const unsubscribe =
      subscribeGCS((event) => {
        if (event.type === "connection") {
          setConnected(
            Boolean(event.connected)
          );

          return;
        }

        if (event.type === "state") {
          setConnected(true);

          const message = event.state;

          if (message?.type === "video_frame") {
            setState((previous) => {
              const updated = {
                ...previous,
                liveImages: {
                  ...(previous.liveImages || {}),
                  [message.source || "drone-rgb"]: message.image,
                },
              };
              stateRef.current = updated;
              return updated;
            });

            return;
          }

          if (message?.type === "ai_event") {
            setState((previous) => {
              let nextRiskEvents = previous.risk_events || {};
              if (message.risk && (message.risk.level === "HIGH" || message.risk.level === "CRITICAL")) {
                const riskId = `risk-ai-${message.frame_id || Date.now()}`;
                const newRisk = {
                  riskId,
                  risk_level: message.risk.level,
                  score: message.risk.score,
                  reason: message.risk.reasons?.[0] || `AI assessed ${message.risk.level} risk`,
                  timestamp: message.timestamp || new Date().toISOString()
                };
                nextRiskEvents = {
                  ...(typeof nextRiskEvents === "object" ? nextRiskEvents : {}),
                  [riskId]: newRisk
                };
              }
              const updated = {
                ...previous,
                ai: message,
                risk: message.risk ?? {
                  level: "LOW",
                  score: 0,
                  reason: "NO ACTIVE HAZARD",
                },
                risk_events: nextRiskEvents
              };
              stateRef.current = updated;
              return updated;
            });

            return;
          }

          if (message?.type === "perception_frame") {
            setState((previous) => {
              let nextRiskEvents = previous.risk_events || {};
              if (message.risk && (message.risk.level === "HIGH" || message.risk.level === "CRITICAL")) {
                const riskId = `risk-ai-${message.frame_id || Date.now()}`;
                const newRisk = {
                  riskId,
                  risk_level: message.risk.level,
                  score: message.risk.score,
                  reason: message.risk.reasons?.[0] || `AI assessed ${message.risk.level} risk`,
                  timestamp: message.timestamp || new Date().toISOString()
                };
                nextRiskEvents = {
                  ...(typeof nextRiskEvents === "object" ? nextRiskEvents : {}),
                  [riskId]: newRisk
                };
              }

              const updated = {
                ...previous,
                ai: message.ai || previous.ai || (message.detections ? { detections: message.detections, risk: message.risk, frame_id: message.frame_id, timestamp: message.timestamp } : null),
                risk: message.risk || previous.risk || null,
                perception: {
                  source: message.source,
                  vehicle_id: message.vehicle_id || message.source,
                  stream_id: message.stream_id,
                  image: message.image,
                  detections: message.detections || [],
                  timestamp: message.timestamp,
                  frame_id: message.frame_id,
                  synchronized: message.synchronized,
                  inference_time_ms: message.inference_time_ms || 0,
                  inference_fps: message.inference_fps || 0,
                  risk: message.risk || null,
                },
                risk_events: nextRiskEvents,
              };
              stateRef.current = updated;
              return updated;
            });

            return;
          }

          const rawState =
            message?.type === "state" && message?.state
              ? message.state
              : message;

          const normalized = normalizeGCSState(rawState);
          stateRef.current = {
            ...normalized,
            liveImages: {
              ...(stateRef.current.liveImages || {}),
              ...(normalized.liveImages || {}),
            },
            ai: normalized.ai ?? stateRef.current.ai ?? null,
            risk: normalized.risk ?? stateRef.current.risk ?? null,
            vehicles: {
              ...normalized.vehicles,
              ...stateRef.current.vehicles,
            },
          };
          setState(stateRef.current);
        }

        if (event.type === "error") {
          console.error(
            "GCS socket error:",
            event.error
          );
        }
      });

    connectGCS();

    return () => {
      unsubscribe();
      disconnectGCS();
    };
  }, []);

  // 2. ROS 2 / PX4 rosbridge subscription + 20Hz Throttled State Flush
  useEffect(() => {
    startRosSubscriptions((handler, data) => {
      if (!data) return;

      if (handler === "map") {
        stateRef.current.map = data;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      const nextVehicles = { ...(stateRef.current.vehicles || {}) };

      // Helper to dynamically resolve active vehicle by type from fleet
      const getActiveVehicle = (type) => {
        const found = Object.values(nextVehicles).find(
          (v) => (v.vehicleType || v.type) === type
        );
        return (
          found || {
            vehicleId: `${type.toUpperCase()}-01`,
            vehicleType: type,
            connected: true,
          }
        );
      };

      // Handle Drone Pose
      if (handler === "drone_pose") {
        const drone = getActiveVehicle("drone");
        const droneId = drone.vehicleId;
        const d = nextVehicles[droneId] || {
          ...drone,
          connected: true,
          position: { x: 0, y: 0, z: 0 },
          telemetry: {},
          px4: {},
        };
        const pos = data.pose?.position || { x: 0, y: 0, z: 0 };
        nextVehicles[droneId] = {
          ...d,
          connected: true,
          position: { x: pos.x, y: pos.y, z: pos.z },
          telemetry: { ...(d.telemetry || {}), position: { x: pos.x, y: pos.y, z: pos.z } },
        };
        stateRef.current.vehicles = nextVehicles;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      // Handle Rover Pose
      if (handler === "rover_pose") {
        const rover = getActiveVehicle("rover");
        const roverId = rover.vehicleId;
        const r = nextVehicles[roverId] || {
          ...rover,
          connected: true,
          position: { x: 0, y: 0, z: 0 },
          telemetry: {},
        };
        const pos = data.pose?.pose?.position || { x: 0, y: 0, z: 0 };
        nextVehicles[roverId] = {
          ...r,
          connected: true,
          position: { x: pos.x, y: pos.y, z: pos.z },
          telemetry: { ...(r.telemetry || {}), position: { x: pos.x, y: pos.y, z: pos.z } },
        };
        stateRef.current.vehicles = nextVehicles;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      // Handle Drone Telemetry String
      if (handler === "drone_telemetry") {
        const drone = getActiveVehicle("drone");
        const droneId = drone.vehicleId;
        const d = nextVehicles[droneId] || {
          ...drone,
          connected: true,
          telemetry: {},
        };
        let parsedTel = {};
        try {
          parsedTel = typeof data.data === "string" ? JSON.parse(data.data) : data;
        } catch (_) {}
        nextVehicles[droneId] = {
          ...d,
          connected: true,
          telemetry: { ...(d.telemetry || {}), ...parsedTel },
        };
        stateRef.current.vehicles = nextVehicles;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      // Handle Rover Telemetry String
      if (handler === "rover_telemetry") {
        const rover = getActiveVehicle("rover");
        const roverId = rover.vehicleId;
        const r = nextVehicles[roverId] || {
          ...rover,
          connected: true,
          telemetry: {},
        };
        let parsedTel = {};
        try {
          parsedTel = typeof data.data === "string" ? JSON.parse(data.data) : data;
        } catch (_) {}
        nextVehicles[roverId] = {
          ...r,
          connected: true,
          telemetry: { ...(r.telemetry || {}), ...parsedTel },
        };
        stateRef.current.vehicles = nextVehicles;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      // Handle Rover Environment String
      if (handler === "rover_environment") {
        const rover = getActiveVehicle("rover");
        const roverId = rover.vehicleId;
        const r = nextVehicles[roverId] || {
          ...rover,
          connected: true,
          telemetry: {},
        };
        let parsedEnv = {};
        try {
          parsedEnv = typeof data.data === "string" ? JSON.parse(data.data) : data;
        } catch (_) {}
        nextVehicles[roverId] = {
          ...r,
          connected: true,
          telemetry: {
            ...(r.telemetry || {}),
            environment: { ...((r.telemetry || {}).environment || {}), ...parsedEnv },
          },
        };
        stateRef.current.vehicles = nextVehicles;
        hasPendingRosUpdatesRef.current = true;
        return;
      }

      // Handle PX4 Normalizers
      const px4Drone = getActiveVehicle("drone");
      const droneId = px4Drone.vehicleId;
      const existingDrone = nextVehicles[droneId] || {
        vehicleId: droneId,
        vehicleType: "drone",
        connected: true,
        position: { x: 0, y: 0, z: 0 },
        telemetry: {},
        px4: {},
      };

      const updatedDrone = {
        ...existingDrone,
        connected: true,
        px4: {
          ...(existingDrone.px4 || {}),
          [handler]: data,
        },
      };

      if (handler === "localPosition" && data) {
        updatedDrone.position = {
          x: data.x ?? existingDrone.position?.x ?? 0,
          y: data.y ?? existingDrone.position?.y ?? 0,
          z: data.z ?? existingDrone.position?.z ?? 0,
        };
        updatedDrone.telemetry = {
          ...(updatedDrone.telemetry || {}),
          position: updatedDrone.position,
        };
      }

      if (handler === "battery" && data) {
        updatedDrone.telemetry = {
          ...(updatedDrone.telemetry || {}),
          battery: data.battery,
          voltage: data.voltage,
        };
      }

      if (handler === "status" && data) {
        updatedDrone.telemetry = {
          ...(updatedDrone.telemetry || {}),
          armed: data.armed,
          navState: data.navState,
          failsafe: data.failsafe,
        };
      }

      nextVehicles[droneId] = updatedDrone;
      stateRef.current.vehicles = nextVehicles;
      hasPendingRosUpdatesRef.current = true;
    });

    // Flush buffered state updates at ~20Hz (every 50ms)
    const interval = setInterval(() => {
      if (hasPendingRosUpdatesRef.current) {
        hasPendingRosUpdatesRef.current = false;
        setState({
          ...stateRef.current,
          vehicles: { ...stateRef.current.vehicles },
        });
      }
    }, 50);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const vehicles = useMemo(
    () =>
      Object.values(
        state.vehicles ?? {}
      ),
    [state.vehicles]
  );

  const vehicleIdsKey = useMemo(
    () => Object.keys(state.vehicles ?? {}).sort().join(","),
    [state.vehicles]
  );

  useEffect(() => {
    if (vehicles.length === 0) {
      setSelectedVehicleId(null);
      return;
    }

    const selectedStillExists =
      vehicles.some(
        (vehicle) =>
          getVehicleId(vehicle) ===
          selectedVehicleId
      );

    if (!selectedStillExists) {
      setSelectedVehicleId(
        getVehicleId(vehicles[0])
      );
    }
  }, [
    vehicleIdsKey,
    selectedVehicleId,
  ]);

  const selectedVehicle =
    vehicles.find(
      (vehicle) =>
        getVehicleId(vehicle) ===
        selectedVehicleId
    ) ?? null;

  const drones = useMemo(
    () =>
      vehicles.filter(
        (vehicle) =>
          getVehicleType(vehicle) ===
          "drone"
      ),
    [vehicles]
  );

  const rovers = useMemo(
    () =>
      vehicles.filter(
        (vehicle) =>
          getVehicleType(vehicle) ===
          "rover"
      ),
    [vehicles]
  );

  const value = useMemo(
    () => ({
      state,

      connected,

      vehicles,

      drones,

      rovers,

      selectedVehicleId,

      selectedVehicle,

      setSelectedVehicleId,
    }),
    [
      state,
      connected,
      vehicles,
      drones,
      rovers,
      selectedVehicleId,
      selectedVehicle,
    ]
  );

  return (
    <GCSStateContext.Provider
      value={value}
    >
      {children}
    </GCSStateContext.Provider>
  );
}

export function useGCSState() {
  const context =
    useContext(GCSStateContext);

  if (!context) {
    throw new Error(
      "useGCSState must be used inside GCSStateProvider"
    );
  }

  return context;
}

function getVehicleId(vehicle) {
  return (
    vehicle?.vehicleId ??
    vehicle?.vehicle_id ??
    null
  );
}

function getVehicleType(vehicle) {
  return (
    vehicle?.vehicleType ??
    vehicle?.vehicle_type ??
    "unknown"
  ).toLowerCase();
}
