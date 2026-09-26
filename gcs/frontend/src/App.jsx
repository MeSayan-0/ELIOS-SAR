import { useCallback, useEffect, useMemo, useState } from "react";
import { Responsive as ResponsiveV2 } from "react-grid-layout";
import { Responsive as ResponsiveLegacy, WidthProvider as WidthProviderLegacy } from "react-grid-layout/legacy";

import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

import "./App.css";
import { useGCSState } from "./state/GCSStateContext.jsx";
import LiveMap from "./LiveMap";
import LiveFeed from "./components/LiveFeed";
import PanelWindow from "./components/PanelWindow";
import VehicleSelector from "./components/VehicleSelector";
import CommandPage from "./CommandPage";
import {
  getControlAuthority,
  enableControl,
  disableControl,
  sendCommand,
  getCommandLog,
  emergencyStop,
} from "./services/commandApi";
import { getSystemEvents } from "./services/systemEventApi";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const Responsive = ResponsiveLegacy || ResponsiveV2;
const WidthProvider = WidthProviderLegacy;
const GridLayout = WidthProvider(Responsive);

/* ------------------------------------------------------------------ */
/* Workspace definitions                                                */
/* ------------------------------------------------------------------ */

const WORKSPACES = {
  Operations: [
    {
      id: "global-map",
      title: "GLOBAL MINE MAP",
      type: "global-map",
    },
    {
      id: "vehicle-status",
      title: "VEHICLE STATUS",
      type: "vehicle-status",
    },
    {
      id: "telemetry",
      title: "TELEMETRY",
      type: "telemetry",
    },
    {
      id: "alerts",
      title: "PRIORITY ALERTS",
      type: "alerts",
    },
    {
      id: "mission-summary",
      title: "MISSION SUMMARY",
      type: "mission-summary",
    },
    {
      id: "event-log",
      title: "EVENT LOG",
      type: "event-log",
    },
  ],

  Missions: [
    {
      id: "mission-control",
      title: "MISSION CONTROL",
      type: "mission-control",
    },
    {
      id: "alerts",
      title: "PRIORITY ALERTS",
      type: "alerts",
    },
    {
      id: "event-log",
      title: "EVENT LOG",
      type: "event-log",
    },
  ],

  Command: [
    {
      id: "command",
      title: "VEHICLE COMMAND CONSOLE",
      type: "command",
    },
  ],

  Recon: [
    {
      id: "recon-feed",
      title: "LIVE RECON",
      type: "recon-feed",
    },
    {
      id: "detections",
      title: "DETECTIONS",
      type: "detections",
    },
    {
      id: "telemetry",
      title: "TELEMETRY",
      type: "telemetry",
    },
    {
      id: "local-lidar",
      title: "LOCAL LIDAR",
      type: "local-lidar",
    },
  ],

  Mapping: [
    {
      id: "mapping-main",
      title: "MAPPING",
      type: "mapping-main",
    },
    {
      id: "global-map",
      title: "GLOBAL MAP",
      type: "global-map",
    },
    {
      id: "local-lidar",
      title: "LOCAL LIDAR",
      type: "local-lidar",
    },
    {
      id: "telemetry",
      title: "TELEMETRY",
      type: "telemetry",
    },
  ],

  Environment: [
    {
      id: "environment-overview",
      title: "ENVIRONMENT",
      type: "environment-overview",
    },
    {
      id: "sensor-inventory",
      title: "SENSOR INVENTORY",
      type: "sensor-inventory",
    },
    {
      id: "environment-timeline",
      title: "ENVIRONMENTAL TIMELINE",
      type: "environment-timeline",
    },
  ],

  System: [
    {
      id: "connection",
      title: "CONNECTION",
      type: "connection",
    },
    {
      id: "telemetry",
      title: "TELEMETRY",
      type: "telemetry",
    },
    {
      id: "event-log",
      title: "EVENT LOG",
      type: "event-log",
    },
    {
      id: "alerts",
      title: "ALERTS",
      type: "alerts",
    },
  ],
};

/* ------------------------------------------------------------------ */
/* Default grid layouts                                                 */
/* ------------------------------------------------------------------ */

const DEFAULT_LAYOUTS = {
  /* ================================================================ */
  /* OPERATIONS                                                       */
  /* ================================================================ */

  Operations: {
    lg: [
      {
        i: "global-map",
        x: 0,
        y: 0,
        w: 8,
        h: 8,
        minW: 5,
        minH: 5,
      },

      {
        i: "vehicle-status",
        x: 8,
        y: 0,
        w: 4,
        h: 8,
        minW: 3,
        minH: 3,
      },

      {
        i: "telemetry",
        x: 0,
        y: 8,
        w: 4,
        h: 4,
        minW: 3,
        minH: 3,
      },

      {
        i: "alerts",
        x: 4,
        y: 8,
        w: 4,
        h: 4,
        minW: 3,
        minH: 3,
      },

      {
        i: "mission-summary",
        x: 8,
        y: 8,
        w: 4,
        h: 4,
        minW: 3,
        minH: 3,
      },

      {
        i: "event-log",
        x: 0,
        y: 12,
        w: 12,
        h: 3,
        minW: 6,
        minH: 2,
      },
    ],
  },

  /* ================================================================ */
  /* MISSIONS                                                         */
  /* ================================================================ */

  Missions: {
    lg: [
      {
        i: "mission-control",
        x: 0,
        y: 0,
        w: 8,
        h: 8,
        minW: 5,
        minH: 5,
      },

      {
        i: "alerts",
        x: 8,
        y: 0,
        w: 4,
        h: 8,
        minW: 3,
        minH: 4,
      },

      {
        i: "event-log",
        x: 0,
        y: 8,
        w: 12,
        h: 4,
        minW: 6,
        minH: 3,
      },
    ],
  },

  /* ================================================================ */
  /* COMMAND                                                          */
  /* ================================================================ */

  Command: {
    lg: [
      {
        i: "command",
        x: 0,
        y: 0,
        w: 12,
        h: 15,
        minW: 8,
        minH: 8,
      },
    ],
  },

  /* ================================================================ */
  /* RECON                                                            */
  /* ================================================================ */

  Recon: {
    lg: [
      {
        i: "recon-feed",
        x: 0,
        y: 0,
        w: 8,
        h: 10,
        minW: 5,
        minH: 6,
      },

      {
        i: "detections",
        x: 8,
        y: 0,
        w: 4,
        h: 10,
        minW: 3,
        minH: 4,
      },

      {
        i: "telemetry",
        x: 0,
        y: 10,
        w: 6,
        h: 5,
        minW: 3,
        minH: 3,
      },

      {
        i: "local-lidar",
        x: 6,
        y: 10,
        w: 6,
        h: 5,
        minW: 3,
        minH: 3,
      },
    ],
  },

  /* ================================================================ */
  /* MAPPING                                                          */
  /* ================================================================ */

  Mapping: {
    lg: [
      {
        i: "mapping-main",
        x: 0,
        y: 0,
        w: 8,
        h: 9,
        minW: 5,
        minH: 5,
      },

      {
        i: "global-map",
        x: 8,
        y: 0,
        w: 4,
        h: 9,
        minW: 3,
        minH: 4,
      },

      {
        i: "local-lidar",
        x: 0,
        y: 9,
        w: 6,
        h: 5,
        minW: 3,
        minH: 3,
      },

      {
        i: "telemetry",
        x: 6,
        y: 9,
        w: 6,
        h: 5,
        minW: 3,
        minH: 3,
      },
    ],
  },

  /* ================================================================ */
  /* ENVIRONMENT                                                      */
  /* ================================================================ */

  Environment: {
    lg: [
      {
        i: "environment-overview",
        x: 0,
        y: 0,
        w: 8,
        h: 7,
        minW: 5,
        minH: 4,
      },

      {
        i: "sensor-inventory",
        x: 8,
        y: 0,
        w: 4,
        h: 7,
        minW: 3,
        minH: 4,
      },

      {
        i: "environment-timeline",
        x: 0,
        y: 7,
        w: 12,
        h: 7,
        minW: 6,
        minH: 4,
      },
    ],
  },

  /* ================================================================ */
  /* SYSTEM                                                           */
  /* ================================================================ */

  System: {
    lg: [
      {
        i: "connection",
        x: 0,
        y: 0,
        w: 4,
        h: 5,
        minW: 3,
        minH: 3,
      },

      {
        i: "telemetry",
        x: 4,
        y: 0,
        w: 4,
        h: 5,
        minW: 3,
        minH: 3,
      },

      {
        i: "alerts",
        x: 8,
        y: 0,
        w: 4,
        h: 5,
        minW: 3,
        minH: 3,
      },

      {
        i: "event-log",
        x: 0,
        y: 5,
        w: 12,
        h: 6,
        minW: 6,
        minH: 4,
      },
    ],
  },
};

/* ------------------------------------------------------------------ */
/* Shared readout atom                                                  */
/* ------------------------------------------------------------------ */

function Readout({ label, value }) {
  return (
    <div className="readout">
      <span className="readout-label">{label}</span>
      <span className="readout-value">{value}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Empty-state placeholder                                             */
/* ------------------------------------------------------------------ */

function NoData({ message }) {
  return (
    <div className="no-data-placeholder">
      {message}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Real LiDAR View component                                           */
/* ------------------------------------------------------------------ */

function LidarView({ scan }) {
  const ranges = Array.isArray(scan?.ranges)
    ? scan.ranges
    : [];

  if (ranges.length === 0) {
    return <NoData message="NO LIDAR DATA" />;
  }

  return (
    <div className="lidar-panel">
      <div className="lidar-real-view">
        <div className="lidar-crosshairs">
          <div className="lidar-ch-h" />
          <div className="lidar-ch-v" />
          <div className="lidar-ring r1" />
          <div className="lidar-ring r2" />
          <div className="lidar-ring r3" />
        </div>
        {ranges.map((range, index) => {
          if (!Number.isFinite(range) || range <= 0) {
            return null;
          }

          const angle =
            (scan.angle_min ?? 0) +
            index * (scan.angle_increment ?? 0.01745);

          const maxRange =
            scan.range_max || 10;

          const radius =
            (Math.min(range, maxRange) / maxRange) * 45;

          const x =
            50 + radius * Math.cos(angle);

          const y =
            50 - radius * Math.sin(angle);

          return (
            <span
              key={index}
              className="lidar-point"
              style={{
                left: `${x}%`,
                top: `${y}%`,
              }}
            />
          );
        })}
      </div>
      <div className="lidar-meta">
        <span>POINTS: {ranges.length}</span>
        <span>RANGE MAX: {scan.range_max ?? 10}m</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Panel content — real backend data only                              */
/* ------------------------------------------------------------------ */

function PanelContent({
  type,
  gcsState,
  gcsConnected,
  selectedVehicleId,
  selectedMissionId,
  onSelectMission,
  controlAuthority,
  commandBusy,
  drones,
  selectedDroneId,
  setSelectedDroneId,
  rover,
  roverSpeed,
  setRoverSpeed,
  commandLog,
  environmentHistory,
  systemEvents,
  vehicles,
  onEnableControl,
  onDisableControl,
  onEmergencyStop,
  onDroneCommand,
  onRoverCommand,
}) {
  switch (type) {

    /* ------ command console ---------------------------------------- */
    case "command":
      return (
        <CommandPage
          controlAuthority={controlAuthority}
          commandBusy={commandBusy}
          drones={drones}
          selectedDroneId={selectedDroneId}
          setSelectedDroneId={setSelectedDroneId}
          rover={rover}
          roverSpeed={roverSpeed}
          setRoverSpeed={setRoverSpeed}
          commandLog={commandLog}
          onEnableControl={onEnableControl}
          onDisableControl={onDisableControl}
          onEmergencyStop={onEmergencyStop}
          onDroneCommand={onDroneCommand}
          onRoverCommand={onRoverCommand}
        />
      );

    /* ------ vehicle status ----------------------------------------- */
    case "vehicle-status": {
      const vehicleIds = Object.keys(gcsState.vehicles ?? {});

      if (vehicleIds.length === 0) {
        return <NoData message="NO VEHICLES CONNECTED" />;
      }

      return (
        <div className="vehicle-status-list">
          {vehicleIds.map((id) => {
            const vehicle = gcsState.vehicles[id];

            const connected =
              vehicle?.connected === true;

            const vehicleType =
              vehicle?.vehicle_type ??
              vehicle?.vehicleType ??
              "UNKNOWN";

            return (
              <div
                key={id}
                className="vehicle-status-card"
              >
                <div className="vehicle-status-main">
                  <span
                    className={
                      connected
                        ? "status-dot online"
                        : "status-dot offline"
                    }
                  />

                  <div className="vehicle-status-name">
                    {id}
                  </div>
                </div>

                <div className="vehicle-status-type">
                  {vehicleType}
                </div>

                <div
                  className={
                    connected
                      ? "vehicle-status-state online"
                      : "vehicle-status-state offline"
                  }
                >
                  {connected
                    ? "CONNECTED"
                    : "DISCONNECTED"}
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    /* ------ mission summary ---------------------------------------- */
    case "mission-summary": {
      const missions = Object.values(
        gcsState.missions ?? {}
      );

      if (missions.length === 0) {
        return <NoData message="NO ACTIVE MISSIONS" />;
      }

      return (
        <div className="mission-summary-list">
          {missions.slice(0, 6).map((mission) => (
            <div
              key={mission.mission_id ?? mission.missionId}
              className="mission-summary-row"
            >
              <div>
                <span className="summary-label">
                  MISSION
                </span>

                <strong>
                  {mission.mission_id ?? mission.missionId ?? "—"}
                </strong>
              </div>

              <div>
                <span className="summary-label">
                  VEHICLE
                </span>

                <strong>
                  {mission.assigned_vehicle_id ?? mission.vehicleId ?? "—"}
                </strong>
              </div>

              <div>
                <span className="summary-label">
                  STATUS
                </span>

                <strong>
                  {mission.status ?? mission.data?.status ?? "—"}
                </strong>
              </div>
            </div>
          ))}
        </div>
      );
    }

    /* ------ add recon feed button/panel ---------------------------- */
    case "add-feed":
      return (
        <div className="add-feed-panel">
          <button
            type="button"
            className="add-feed-button"
          >
            <span className="add-feed-icon">+</span>
            <span>
              ADD RECON FEED
            </span>
          </button>

          <span className="add-feed-description">
            RGB / THERMAL / SPLIT feeds can be added here when a real media source is available.
          </span>
        </div>
      );

    /* ------ recon hero feed ---------------------------------------- */
    case "recon-feed":
    case "drone-feed":
    case "thermal-feed":
      return (
        <LiveFeed
          title="LIVE RECON"
          vehicles={vehicles}
          selectedVehicleId={selectedVehicleId}
          liveImages={gcsState?.liveImages || {}}
        />
      );

    /* ------ global map & mapping-main ------------------------------ */
    case "global-map":
    case "mapping-main": {
      const mapData = gcsState?.map;

      if (!mapData) {
        return <NoData message="NO MAP DATA" />;
      }

      return (
        <div className="map-panel">
          <LiveMap
            mapData={mapData}
            vehicles={gcsState.vehicles}
            detections={
              gcsState.detections && Object.keys(gcsState.detections).length > 0
                ? gcsState.detections
                : gcsState.persons
            }
            hazards={gcsState.hazards}
            risks={gcsState.risk_events}
          />

          <div className="map-footer">
            <span>
              MAP: STREAMING
            </span>

            <span>
              GRID:{" "}
              {mapData.resolution !== undefined
                ? `${mapData.resolution} m`
                : "—"}
            </span>

            <span>
              SIZE:{" "}
              {mapData.width ?? "—"} × {mapData.height ?? "—"}
            </span>

            <span>
              VEHICLES:{" "}
              {Object.keys(
                gcsState.vehicles || {}
              ).length}
            </span>
          </div>
        </div>
      );
    }

    /* ------ local lidar -------------------------------------------- */
    case "local-lidar": {
      const vehicle =
        selectedVehicleId
          ? gcsState?.vehicles?.[selectedVehicleId]
          : (Object.values(gcsState?.vehicles ?? {})[0] ?? null);

      const scan =
        vehicle?.lidar ??
        vehicle?.scan ??
        gcsState?.scan ??
        null;

      if (!scan) {
        return <NoData message="NO LIDAR DATA" />;
      }

      return <LidarView scan={scan} />;
    }

    /* ------ telemetry ---------------------------------------------- */
    case "telemetry": {
      const vehicleIds = Object.keys(gcsState?.vehicles ?? {});

      if (vehicleIds.length === 0) {
        return <NoData message="NO VEHICLE CONNECTED" />;
      }

      const activeId =
        selectedVehicleId && gcsState?.vehicles?.[selectedVehicleId]
          ? selectedVehicleId
          : vehicleIds[0];

      const vehicle = gcsState?.vehicles?.[activeId] ?? {};
      const telemetry = vehicle?.telemetry ?? {};
      const pos = telemetry?.position ?? vehicle?.position;

      return (
        <div className="telemetry-grid">
          <Readout label="VEHICLE" value={activeId} />
          <Readout label="TYPE" value={vehicle?.vehicle_type ?? vehicle?.vehicleType ?? "—"} />
          <Readout label="MODE" value={telemetry?.flight_mode ?? vehicle?.flight_mode ?? "—"} />
          <Readout
            label="BATTERY"
            value={
              telemetry?.battery !== undefined
                ? (typeof telemetry.battery === "object"
                    ? `${telemetry.battery?.percentage?.toFixed(1) ?? "—"}%`
                    : `${Number(telemetry.battery).toFixed(1)}%`)
                : (vehicle?.battery !== undefined
                    ? `${Number(vehicle.battery).toFixed(1)}%`
                    : "—")
            }
          />
          <Readout
            label="ALTITUDE"
            value={
              telemetry?.altitude !== undefined
                ? `${Number(telemetry.altitude).toFixed(2)} m`
                : (pos?.z !== undefined ? `${Number(pos.z).toFixed(2)} m` : "—")
            }
          />
          <Readout
            label="SPEED"
            value={
              telemetry?.speed !== undefined
                ? `${Number(telemetry.speed).toFixed(2)} m/s`
                : "—"
            }
          />
          <Readout
            label="HEADING"
            value={
              telemetry?.heading !== undefined
                ? `${Number(telemetry.heading).toFixed(1)}°`
                : "—"
            }
          />
          <Readout
            label="LINK"
            value={vehicle?.connected !== false ? "CONNECTED" : "DISCONNECTED"}
          />
          <Readout
            label="ARMED"
            value={
              telemetry?.armed === true || vehicle?.armed === true
                ? "ARMED"
                : telemetry?.armed === false || vehicle?.armed === false
                  ? "DISARMED"
                  : "—"
            }
          />
        </div>
      );
    }

    /* ------ alerts ------------------------------------------------- */
    case "alerts": {
      const risks = Array.isArray(gcsState.risk_events)
        ? gcsState.risk_events
        : Object.values(gcsState.risk_events || {});

      const hazards = Array.isArray(gcsState.hazards)
        ? gcsState.hazards
        : Object.values(gcsState.hazards || {});

      const hasRisks   = risks.length > 0;
      const hasHazards = hazards.length > 0;

      if (!hasRisks && !hasHazards) {
        return <NoData message="NO ACTIVE ALERTS" />;
      }

      return (
        <div className="alert-list">
          {risks.slice(-5).reverse().map((risk, idx) => {
            const level = (risk.risk_level ?? risk.data?.risk_level ?? "RISK").toUpperCase();
            const reason = risk.reason ?? risk.data?.reason ?? "Risk event";
            const score = risk.score ?? risk.data?.score;
            const isCritical = level === "HIGH" || level === "CRITICAL";

            return (
              <div
                key={`risk-${idx}`}
                className={`alert-row ${isCritical ? "alert-warning" : "alert-normal"}`}
              >
                <span className="alert-state">{level}</span>
                <span>{reason}</span>
                <span className="alert-time">
                  {score !== undefined ? Number(score).toFixed(0) : "—"}
                </span>
              </div>
            );
          })}

          {hasHazards && hazards.slice(-3).reverse().map((hz, idx) => {
            const severity = (hz.severity ?? hz.data?.severity ?? "HAZARD").toUpperCase();
            const hazardType = hz.hazard_type ?? hz.hazardType ?? hz.data?.hazard_type ?? "Hazard";

            return (
              <div key={`hz-${idx}`} className="alert-row alert-warning">
                <span className="alert-state">{severity}</span>
                <span>{hazardType} detected</span>
                <span className="alert-time">HAZARD</span>
              </div>
            );
          })}
        </div>
      );
    }

    /* ------ event log (system events) ------------------------------ */
    case "event-log": {
      if (!systemEvents || systemEvents.length === 0) {
        return (
          <NoData message="NO SYSTEM EVENTS" />
        );
      }

      return (
        <div className="event-log">
          <div className="event-row event-heading">
            <span>TIME</span>
            <span>LEVEL</span>
            <span>SOURCE</span>
            <span>EVENT</span>
          </div>

          {systemEvents.map((event, index) => (
            <div
              className="event-row"
              key={event._id ?? `${event.timestamp}-${index}`}
            >
              <span>
                {event.timestamp
                  ? new Date(
                      event.timestamp
                    ).toLocaleTimeString()
                  : "—"}
              </span>

              <span className={`event-level ${(event.level || "INFO").toLowerCase()}`}>
                {event.level ?? "INFO"}
              </span>

              <span>
                {event.source ?? "—"}
              </span>

              <span>
                {event.message ?? "—"}
              </span>
            </div>
          ))}
        </div>
      );
    }

    /* ------ environment overview (graph + readouts) --------------- */
    case "environment-overview": {
      if (!environmentHistory || environmentHistory.length === 0) {
        return (
          <NoData message="NO ENVIRONMENT DATA" />
        );
      }

      const latest =
        environmentHistory[environmentHistory.length - 1];

      return (
        <div className="environment-panel">
          <div className="environment-chart">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={environmentHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#252d33" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#737e85"
                  tickFormatter={(value) => {
                    try {
                      return new Date(value).toLocaleTimeString();
                    } catch {
                      return value;
                    }
                  }}
                />
                <YAxis stroke="#737e85" />
                <Tooltip
                  contentStyle={{
                    background: "#1c2328",
                    border: "1px solid #303a41",
                    color: "#d5dadd",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="ch4"
                  name="CH₄"
                  stroke="#c2a36a"
                  dot={false}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="co"
                  name="CO"
                  stroke="#c26a6a"
                  dot={false}
                  connectNulls={false}
                />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  name="Temp (°C)"
                  stroke="#6fa4c2"
                  dot={false}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="environment-readouts">
            <Readout
              label="CH₄"
              value={
                latest.ch4 !== null && latest.ch4 !== undefined
                  ? `${latest.ch4}`
                  : "—"
              }
            />

            <Readout
              label="CO"
              value={
                latest.co !== null && latest.co !== undefined
                  ? `${latest.co}`
                  : "—"
              }
            />

            <Readout
              label="O₂"
              value={
                latest.o2 !== null && latest.o2 !== undefined
                  ? `${latest.o2}`
                  : "—"
              }
            />

            <Readout
              label="TEMPERATURE"
              value={
                latest.temperature !== null && latest.temperature !== undefined
                  ? `${latest.temperature} °C`
                  : "—"
              }
            />

            <Readout
              label="HUMIDITY"
              value={
                latest.humidity !== null && latest.humidity !== undefined
                  ? `${latest.humidity} %`
                  : "—"
              }
            />
          </div>
        </div>
      );
    }

    /* ------ sensor inventory --------------------------------------- */
    case "sensor-inventory": {
      const sensors = Object.values(
        gcsState?.sensors ?? {}
      );

      if (sensors.length === 0) {
        return (
          <NoData message="NO SENSOR DATA" />
        );
      }

      return (
        <div className="sensor-list">
          {sensors.map((sensor, index) => (
            <div
              className="sensor-row"
              key={
                sensor.sensor_id ??
                sensor.sensorId ??
                index
              }
            >
              <span>
                {sensor.sensor_type ??
                  sensor.sensorType ??
                  "SENSOR"}
              </span>

              <span>
                {sensor.value ??
                  sensor.data?.value ??
                  "—"}
              </span>

              <span>
                {sensor.unit ??
                  sensor.data?.unit ??
                  ""}
              </span>

              <span>
                {sensor.vehicle_id ??
                  sensor.vehicleId ??
                  "—"}
              </span>
            </div>
          ))}
        </div>
      );
    }

    /* ------ environment timeline ----------------------------------- */
    case "environment-timeline": {
      if (!environmentHistory || environmentHistory.length === 0) {
        return (
          <NoData message="NO ENVIRONMENT HISTORY" />
        );
      }

      return (
        <div className="environment-timeline">
          {environmentHistory
            .slice()
            .reverse()
            .slice(0, 30)
            .map((row, index) => (
              <div
                className="environment-timeline-row"
                key={index}
              >
                <span>
                  {new Date(
                    row.timestamp
                  ).toLocaleTimeString()}
                </span>

                <span>
                  CH₄: {row.ch4 ?? "—"}
                </span>

                <span>
                  CO: {row.co ?? "—"}
                </span>

                <span>
                  TEMP: {row.temperature ?? "—"}
                </span>

                <span>
                  HUM: {row.humidity ?? "—"}
                </span>
              </div>
            ))}
        </div>
      );
    }

    /* ------ mission control ---------------------------------------- */
    case "mission-control": {
      const missions = Array.isArray(gcsState?.missions)
        ? gcsState.missions
        : Object.values(gcsState?.missions || {});

      return (
        <div className="missions-page">

          <div className="missions-page-header">
            <div>
              <div className="missions-page-title">
                MISSIONS
              </div>

              <div className="missions-page-subtitle">
                {missions.length} mission
                {missions.length === 1 ? "" : "s"} received
                from GCS state
              </div>
            </div>
          </div>

          {missions.length === 0 ? (
            <div className="missions-empty">
              <div className="missions-empty-title">
                NO ACTIVE MISSIONS
              </div>

              <div className="missions-empty-subtitle">
                Mission state will appear here when received
                from the backend.
              </div>
            </div>
          ) : (
            <div className="mission-list">

              {missions.map((mission) => {
                const missionId =
                  mission?.mission_id ??
                  mission?.missionId;

                if (!missionId) {
                  return null;
                }

                const vehicleId =
                  mission?.assigned_vehicle_id ??
                  mission?.vehicle_id ??
                  "UNASSIGNED";

                const status =
                  mission?.status ??
                  "UNKNOWN";

                const timestamp =
                  mission?.timestamp;

                return (
                  <button
                    key={missionId}
                    type="button"
                    className={
                      selectedMissionId === missionId
                        ? "mission-card selected"
                        : "mission-card"
                    }
                    onClick={() =>
                      onSelectMission(missionId)
                    }
                  >

                    <div className="mission-card-header">

                      <div className="mission-card-id">
                        {missionId}
                      </div>

                      <div
                        className={`mission-status-badge ${String(
                          status
                        ).toLowerCase()}`}
                      >
                        {status}
                      </div>

                    </div>

                    <div className="mission-card-info">

                      <div>
                        <span>VEHICLE</span>
                        <strong>
                          {vehicleId}
                        </strong>
                      </div>

                      <div>
                        <span>CREATED</span>
                        <strong>
                          {timestamp
                            ? new Date(
                                timestamp
                              ).toLocaleString()
                            : "—"}
                        </strong>
                      </div>

                      <div>
                        <span>ANCHOR</span>
                        <strong>
                          {mission?.anchor
                            ? JSON.stringify(
                                mission.anchor
                              )
                            : "—"}
                        </strong>
                      </div>

                    </div>

                  </button>
                );
              })}

            </div>
          )}

          {selectedMissionId && (
            <MissionDetailModal
              missionId={selectedMissionId}
              missions={missions}
              gcsState={gcsState}
              onClose={() =>
                onSelectMission(null)
              }
            />
          )}

        </div>
      );
    }

    /* ------ detections --------------------------------------------- */
    case "detections": {
      const rawDetections = Array.isArray(gcsState.detections) && gcsState.detections.length > 0
        ? gcsState.detections
        : (Array.isArray(gcsState.persons) ? gcsState.persons : []);

      if (rawDetections.length === 0) {
        return <NoData message="NO DETECTIONS" />;
      }

      return (
        <div className="detection-list">
          {rawDetections
            .slice()
            .reverse()
            .slice(0, 20)
            .map((detection, index) => {
              const id =
                detection.detection_id ??
                detection.detectionId ??
                `DET-${index + 1}`;

              const conf =
                detection.confidence ??
                detection.data?.confidence;

              const pos =
                detection.position ??
                detection.data?.position;

              const source =
                detection.source ??
                detection.data?.source ??
                detection.label ??
                "—";

              return (
                <div
                  className="detection-row"
                  key={id}
                >
                  <span className="detection-id">
                    {id.length > 14 ? id.slice(0, 10) + "…" : id}
                  </span>

                  <span>
                    {conf !== undefined && Number.isFinite(Number(conf))
                      ? `${Math.round(Number(conf) <= 1 ? Number(conf) * 100 : Number(conf))}%`
                      : "—"}
                  </span>

                  <span>
                    {pos
                      ? `${pos.x !== undefined ? Number(pos.x).toFixed(1) : "—"}, ${pos.y !== undefined ? Number(pos.y).toFixed(1) : "—"}`
                      : "—"}
                  </span>

                  <span>
                    {source}
                  </span>
                </div>
              );
            })}
        </div>
      );
    }

    /* ------ connection --------------------------------------------- */
    case "connection": {
      const vehicleIds = Object.keys(gcsState?.vehicles ?? {});

      return (
        <div className="connection-panel">
          <div className="connection-status">
            <span className="status-dot" />
            <strong>{gcsConnected ? "GCS CONNECTED" : "GCS OFFLINE"}</strong>
          </div>

          <Readout label="TRANSPORT" value="WebSocket" />
          <Readout label="PROTOCOL"  value="JSON" />
          <Readout label="WS STATUS" value={gcsConnected ? "OPEN" : "DISCONNECTED"} />
          <Readout
            label="VEHICLES"
            value={vehicleIds.length > 0 ? vehicleIds.join(", ") : "NONE"}
          />
        </div>
      );
    }

    default:
      return <NoData message="NO DATA" />;
  }
}

function MissionDetailModal({
  missionId,
  missions,
  gcsState,
  onClose,
}) {
  const mission = missions.find(
    (item) =>
      (item?.mission_id ?? item?.missionId) ===
      missionId
  );

  if (!mission) {
    return null;
  }

  const vehicleId =
    mission?.assigned_vehicle_id ??
    mission?.vehicle_id ??
    "UNASSIGNED";

  const status =
    mission?.status ??
    "UNKNOWN";

  const timestamp =
    mission?.timestamp;

  const anchor =
    mission?.anchor;

  /*
   * Mission events are the authoritative timeline
   * available in the current GCS state.
   */
  const missionEvents = Array.isArray(
    gcsState?.mission_events
  )
    ? gcsState.mission_events
        .filter(
          (event) =>
            event?.mission_id === missionId
        )
        .sort((a, b) => {
          const ta = Date.parse(a?.timestamp || "");
          const tb = Date.parse(b?.timestamp || "");

          if (
            Number.isFinite(ta) &&
            Number.isFinite(tb)
          ) {
            return ta - tb;
          }

          return 0;
        })
    : [];

  /*
   * Current backend state contains person detections
   * globally. Only use detections explicitly associated
   * with this mission.
   */
  const missionDetections = Array.isArray(
    gcsState?.persons
  )
    ? gcsState.persons.filter(
        (detection) =>
          detection?.mission_id === missionId
      )
    : [];

  /*
   * The map state is real backend map data.
   *
   * We only display it if the current map belongs to
   * this mission's vehicle or explicitly identifies
   * the mission.
   */
  const mapData = gcsState?.map;

  const mapBelongsToMission =
    mapData &&
    (
      mapData.mission_id === missionId ||
      mapData.vehicle_id === vehicleId
    );

  return (
    <div
      className="mission-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget
        ) {
          onClose();
        }
      }}
    >

      <div
        className="mission-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Mission ${missionId}`}
      >

        {/* HEADER */}
        <div className="mission-modal-header">

          <div>
            <div className="mission-modal-title">
              {missionId}
            </div>

            <div className="mission-modal-subtitle">
              {vehicleId}
            </div>
          </div>

          <button
            type="button"
            className="mission-modal-close"
            onClick={onClose}
            aria-label="Close mission details"
          >
            ×
          </button>

        </div>

        {/* META */}
        <div className="mission-meta-grid">

          <div className="mission-meta-item">
            <span>STATUS</span>
            <strong>{status}</strong>
          </div>

          <div className="mission-meta-item">
            <span>VEHICLE</span>
            <strong>{vehicleId}</strong>
          </div>

          <div className="mission-meta-item">
            <span>CREATED</span>
            <strong>
              {timestamp
                ? new Date(
                    timestamp
                  ).toLocaleString()
                : "—"}
            </strong>
          </div>

          <div className="mission-meta-item">
            <span>ANCHOR</span>
            <strong>
              {anchor
                ? JSON.stringify(anchor)
                : "—"}
            </strong>
          </div>

        </div>

        {/* BODY */}
        <div className="mission-detail-grid">

          {/* LOCAL MAP */}
          <section className="mission-detail-section">

            <div className="mission-section-title">
              LOCAL MAP
            </div>

            <div className="mission-map">

              {mapBelongsToMission ? (
                <LiveMap
                  mapData={mapData}
                  dronePosition={
                    mapData?.drone_position ??
                    null
                  }
                />
              ) : (
                <div className="mission-no-data">
                  NO LOCAL MAP DATA
                </div>
              )}

            </div>

          </section>

          {/* DETECTIONS */}
          <section className="mission-detail-section">

            <div className="mission-section-title">
              DETECTIONS
            </div>

            <div className="mission-detection-list">

              {missionDetections.length === 0 ? (
                <div className="mission-no-data">
                  NO DETECTIONS
                </div>
              ) : (
                missionDetections.map(
                  (detection, index) => {

                    const detectionId =
                      detection?.detection_id ??
                      detection?.person_id ??
                      `DETECTION-${index + 1}`;

                    return (
                      <div
                        key={
                          detectionId
                        }
                        className="mission-detection-row"
                      >

                        <div>
                          <strong>
                            {detectionId}
                          </strong>

                          <span>
                            {detection?.source ??
                              "PERSON DETECTION"}
                          </span>
                        </div>

                        <strong>
                          {typeof detection?.confidence ===
                          "number"
                            ? `${(
                                detection.confidence *
                                100
                              ).toFixed(1)}%`
                            : "—"}
                        </strong>

                      </div>
                    );
                  }
                )
              )}

            </div>

          </section>

        </div>

        {/* TIMELINE */}
        <section className="mission-timeline-section">

          <div className="mission-section-title">
            MISSION TIMELINE
          </div>

          {missionEvents.length === 0 ? (
            <div className="mission-no-data">
              NO MISSION EVENTS
            </div>
          ) : (
            <div className="mission-timeline">

              {missionEvents.map(
                (event, index) => {

                  const time =
                    event?.timestamp
                      ? new Date(
                          event.timestamp
                        ).toLocaleTimeString()
                      : "—";

                  return (
                    <div
                      key={
                        event?.event_id ??
                        `${missionId}-${index}`
                      }
                      className="mission-timeline-row"
                    >

                      <span className="mission-timeline-time">
                        {time}
                      </span>

                      <span className="mission-timeline-type">
                        {event?.event_type ??
                          "EVENT"}
                      </span>

                      <span className="mission-timeline-message">
                        {event?.message ??
                          event?.description ??
                          "Mission event received"}
                      </span>

                    </div>
                  );
                }
              )}

            </div>
          )}

        </section>

      </div>

    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dynamic status bar vehicles                                         */
/* ------------------------------------------------------------------ */

function StatusBarVehicles({ vehicles, gcsConnected }) {
  const ids = Object.keys(vehicles);

  return (
    <>
      {ids.length === 0 ? (
        <div>VEHICLES: NO CONNECTION</div>
      ) : (
        ids.map((id) => {
          const v = vehicles[id];
          const connected = v?.connected !== false;
          return (
            <div key={id}>
              {id.toUpperCase()}:{" "}
              <span className={connected ? "online" : "offline"}>
                {connected ? "● CONNECTED" : "● DISCONNECTED"}
              </span>
            </div>
          );
        })
      )}
      <div>
        GCS:{" "}
        <span className={gcsConnected ? "online" : "offline"}>
          {gcsConnected ? "● CONNECTED" : "● OFFLINE"}
        </span>
      </div>
    </>
  );
}

function cloneLayout(layout) {
  return Array.isArray(layout)
    ? layout.map((item) => ({ ...item }))
    : [];
}

function makeResponsiveLayout(layout, cols) {
  const source = Array.isArray(layout)
    ? layout.map((item) => ({ ...item }))
    : [];

  if (source.length === 0) {
    return [];
  }

  if (cols === 12) {
    return source.map((item) => {
      const safeW = Math.max(
        1,
        Math.min(Number(item.w) || 1, cols)
      );

      const safeX = Math.max(
        0,
        Math.min(Number(item.x) || 0, cols - safeW)
      );

      return {
        ...item,
        x: safeX,
        y: Math.max(0, Number(item.y) || 0),
        w: safeW,
        h: Math.max(1, Number(item.h) || 1),
        minW: Math.min(
          Number(item.minW) || 1,
          safeW
        ),
        minH: Math.min(
          Number(item.minH) || 1,
          Math.max(1, Number(item.h) || 1)
        ),
      };
    });
  }

  /*
   * First normalize every item so that it can physically
   * fit inside the current breakpoint.
   */
  const normalized = source.map((item) => {
    const minW = Math.min(
      Number(item.minW) || 1,
      cols
    );

    const w = Math.max(
      minW,
      Math.min(Number(item.w) || 1, cols)
    );

    return {
      ...item,
      x: 0,
      y: 0,
      w,
      h: Math.max(1, Number(item.h) || 1),
      minW,
      minH: Math.max(
        1,
        Number(item.minH) || 1
      ),
    };
  });

  /*
   * Reflow items row by row.
   *
   * We intentionally create the rows ourselves instead
   * of relying on the old desktop x/y positions.
   */
  const rows = [];
  let currentRow = [];
  let usedColumns = 0;

  normalized.forEach((item) => {
    if (
      currentRow.length > 0 &&
      usedColumns + item.w > cols
    ) {
      rows.push(currentRow);

      currentRow = [];
      usedColumns = 0;
    }

    currentRow.push(item);
    usedColumns += item.w;
  });

  if (currentRow.length > 0) {
    rows.push(currentRow);
  }

  /*
   * Now make every row fill the entire available width.
   *
   * Example:
   *
   * cols = 6
   * widths = [5]
   *
   * becomes:
   *
   * widths = [6]
   *
   * Example:
   *
   * cols = 6
   * widths = [3, 2]
   *
   * becomes:
   *
   * widths = [3, 3]
   *
   * The final panel absorbs the remaining space so
   * there is NEVER an unnecessary blank area on the right.
   */
  let y = 0;

  const result = [];

  rows.forEach((row) => {
    let totalWidth = row.reduce(
      (sum, item) => sum + item.w,
      0
    );

    const remaining = cols - totalWidth;

    if (remaining > 0 && row.length > 0) {
      /*
       * Give the remaining columns to the last panel.
       *
       * This is safer than changing every panel's width
       * and preserves the original proportions as much
       * as possible.
       */
      row[row.length - 1] = {
        ...row[row.length - 1],
        w:
          row[row.length - 1].w +
          remaining,
      };
    }

    let x = 0;
    let rowHeight = 1;

    row.forEach((item) => {
      const nextItem = {
        ...item,
        x,
        y,
      };

      result.push(nextItem);

      x += nextItem.w;

      rowHeight = Math.max(
        rowHeight,
        nextItem.h
      );
    });

    y += rowHeight;
  });

  return result;
}

/* ------------------------------------------------------------------ */
/* App                                                                 */
/* ------------------------------------------------------------------ */

function App() {
  const {
    state: gcsState,
    connected: gcsConnected,
    vehicles,
    drones,
    rovers,
    selectedVehicleId,
    selectedVehicle,
    setSelectedVehicleId,
  } = useGCSState();

  const [activeWorkspace, setActiveWorkspace] = useState("Operations");
  const [selectedMissionId, setSelectedMissionId] = useState(null);
  const [fullscreenPanelId, setFullscreenPanelId] = useState(null);
  const [layouts, setLayouts] = useState(DEFAULT_LAYOUTS);

  const [controlAuthority, setControlAuthority] = useState({
    enabled: false,
    enabledAt: null,
  });
  const [commandLog, setCommandLog] = useState([]);
  const [selectedDroneId, setSelectedDroneId] = useState(null);
  const [roverSpeed, setRoverSpeed] = useState(0.5);
  const [commandBusy, setCommandBusy] = useState(false);

  const [environmentHistory, setEnvironmentHistory] = useState([]);
  const [systemEvents, setSystemEvents] = useState([]);
  const [clock, setClock] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const alerts = useMemo(
    () => (Array.isArray(gcsState?.alerts) ? gcsState.alerts : []),
    [gcsState?.alerts]
  );

  const controlEnabled = Boolean(controlAuthority?.enabled);

  const px4 = useMemo(() => {
    const droneWithPx4 = drones.find(
      (d) => d?.px4 && Object.keys(d.px4).length > 0
    );
    const px4Data = droneWithPx4?.px4 ?? {};
    const status = px4Data.status ?? {};
    const isConnected = Boolean(
      droneWithPx4 &&
        droneWithPx4.connected !== false &&
        Object.keys(px4Data).length > 0
    );
    const isArmed = Boolean(
      status.armed ?? droneWithPx4?.telemetry?.armed ?? false
    );
    return {
      connected: isConnected,
      armed: isArmed,
    };
  }, [drones]);

  useEffect(() => {
    const vList = Object.values(gcsState?.vehicles ?? {});
    const samples = [];

    for (const vehicle of vList) {
      const telemetry = vehicle?.telemetry ?? {};
      const environment =
        telemetry.environment ?? vehicle?.environment ?? {};

      if (!environment || Object.keys(environment).length === 0) {
        continue;
      }

      const timestamp = telemetry.timestamp ?? vehicle.lastSeen;
      if (!timestamp) continue;

      samples.push({
        timestamp,
        ch4: environment.ch4 ?? environment.methane ?? null,
        co: environment.co ?? null,
        o2: environment.o2 ?? null,
        temperature: environment.temperature ?? null,
        humidity: environment.humidity ?? null,
      });
    }

    if (samples.length > 0) {
      setEnvironmentHistory((previous) => {
        const lastTimestamp = previous.length > 0 ? previous[previous.length - 1].timestamp : null;
        const newSamples = samples.filter((s) => s.timestamp !== lastTimestamp);
        if (newSamples.length === 0) return previous;
        const merged = [...previous, ...newSamples];
        return merged.slice(-120);
      });
    }
  }, [gcsState]);

  const refreshSystemEvents = useCallback(async () => {
    try {
      const result = await getSystemEvents(100);
      if (Array.isArray(result?.events)) {
        setSystemEvents(result.events);
      }
    } catch (error) {
      // non-blocking
    }
  }, []);

  useEffect(() => {
    refreshSystemEvents();
    const interval = setInterval(refreshSystemEvents, 3000);
    return () => clearInterval(interval);
  }, [refreshSystemEvents]);

  useEffect(() => {
    if (!selectedDroneId && drones.length > 0) {
      setSelectedDroneId(drones[0].vehicleId || drones[0].id);
    }
  }, [drones, selectedDroneId]);

  const refreshCommandData = useCallback(async () => {
    try {
      const authority = await getControlAuthority();
      if (authority?.authority) {
        setControlAuthority(authority.authority);
      } else if (authority) {
        setControlAuthority(authority);
      }

      const log = await getCommandLog();
      if (Array.isArray(log)) {
        setCommandLog(log);
      } else if (Array.isArray(log?.commands)) {
        setCommandLog(log.commands);
      } else {
        setCommandLog([]);
      }
    } catch (error) {
      console.warn("Failed to load command data:", error?.message || error);
    }
  }, []);

  useEffect(() => {
    refreshCommandData();
    const interval = setInterval(refreshCommandData, 3000);
    return () => clearInterval(interval);
  }, [refreshCommandData]);

  const handleEnableControl = async () => {
    try {
      setCommandBusy(true);
      const result = await enableControl();
      if (result?.authority) {
        setControlAuthority(result.authority);
      }
      await refreshCommandData();
      await refreshSystemEvents();
    } catch (error) {
      console.error("Failed to enable GCS control:", error);
    } finally {
      setCommandBusy(false);
    }
  };

  const handleDisableControl = async () => {
    try {
      setCommandBusy(true);
      const result = await disableControl();
      if (result?.authority) {
        setControlAuthority(result.authority);
      }
      await refreshCommandData();
      await refreshSystemEvents();
    } catch (error) {
      console.error("Failed to disable GCS control:", error);
    } finally {
      setCommandBusy(false);
    }
  };

  const handleCommand = async (vehicleId, command, metadata = {}) => {
    if (!vehicleId) {
      window.alert("NO VEHICLE SELECTED");
      return;
    }

    if (!controlAuthority.enabled) {
      window.alert("GCS CONTROL IS DISABLED");
      return;
    }

    try {
      setCommandBusy(true);
      await sendCommand({
        vehicleId,
        command,
        metadata,
      });
      await refreshCommandData();
      await refreshSystemEvents();
    } catch (error) {
      console.error(`Command ${command} failed:`, error);
      window.alert(`Command failed: ${error.message}`);
    } finally {
      setCommandBusy(false);
    }
  };

  const handleEmergencyStop = async () => {
    const confirmed = window.confirm("EMERGENCY STOP ALL ACTIVE VEHICLES?");
    if (!confirmed) return;

    try {
      setCommandBusy(true);
      const allIds = vehicles.map((v) => v.vehicleId || v.id).filter(Boolean);
      await emergencyStop(allIds);
      await refreshCommandData();
      await refreshSystemEvents();
    } catch (error) {
      console.error("Emergency stop failed:", error);
    } finally {
      setCommandBusy(false);
    }
  };

  const handleDroneCommand = (command) => {
    if (!selectedDroneId) {
      window.alert("NO DRONE SELECTED");
      return;
    }
    handleCommand(selectedDroneId, command);
  };

  const selectedRover = rovers.length > 0 ? rovers[0] : null;
  const selectedRoverId = selectedRover?.vehicleId || selectedRover?.id || null;

  const handleRoverCommand = (command) => {
    if (!selectedRoverId) {
      window.alert("NO ROVER CONNECTED");
      return;
    }
    handleCommand(selectedRoverId, command, { speed: roverSpeed });
  };

  const [visiblePanels, setVisiblePanels] = useState(() =>
    Object.fromEntries(
      Object.entries(WORKSPACES).map(([ws, panels]) => [
        ws,
        panels.map((p) => p.id),
      ])
    )
  );

  const activePanels = useMemo(() => {
    const ids = visiblePanels[activeWorkspace] ?? [];
    return WORKSPACES[activeWorkspace].filter((p) => ids.includes(p.id));
  }, [activeWorkspace, visiblePanels]);

  const activeFullscreenPanel = useMemo(() => {
    if (!fullscreenPanelId) return null;
    return WORKSPACES[activeWorkspace].find((p) => p.id === fullscreenPanelId) ?? null;
  }, [activeWorkspace, fullscreenPanelId]);

  const currentLayout =
    layouts[activeWorkspace] ??
    DEFAULT_LAYOUTS[activeWorkspace];

  const safeCurrentLayout = useMemo(() => {
    const base = currentLayout ?? {};

    const lg = makeResponsiveLayout(
      base.lg ?? [],
      12
    );

    const md = makeResponsiveLayout(
      base.md ?? lg,
      12
    );

    const sm = makeResponsiveLayout(
      base.sm ?? md,
      6
    );

    const xs = makeResponsiveLayout(
      base.xs ?? sm,
      4
    );

    return {
      lg,
      md,
      sm,
      xs,
    };
  }, [currentLayout]);

  function closePanel(panelId) {
    if (fullscreenPanelId === panelId) setFullscreenPanelId(null);
    setVisiblePanels((prev) => ({
      ...prev,
      [activeWorkspace]: prev[activeWorkspace].filter((id) => id !== panelId),
    }));
  }

  function toggleFullscreen(panelId) {
    setFullscreenPanelId((prev) => (prev === panelId ? null : panelId));
  }

  function resetWorkspace() {
    setFullscreenPanelId(null);

    const defaultLayout = JSON.parse(
      JSON.stringify(DEFAULT_LAYOUTS[activeWorkspace])
    );

    setLayouts((previous) => ({
      ...previous,
      [activeWorkspace]: defaultLayout,
    }));

    setVisiblePanels((previous) => ({
      ...previous,
      [activeWorkspace]: WORKSPACES[activeWorkspace].map(
        (panel) => panel.id
      ),
    }));
  }

  function handleLayoutChange(nextLayout, allLayouts) {
    setLayouts((prev) => {
      const existing =
        prev[activeWorkspace] ??
        DEFAULT_LAYOUTS[activeWorkspace] ??
        {};

      return {
        ...prev,

        [activeWorkspace]: {
          ...existing,

          ...(allLayouts ?? {
            lg: nextLayout,
          }),
        },
      };
    });
  }

  function changeWorkspace(workspace) {
    setFullscreenPanelId(null);
    setSelectedMissionId(null);
    setActiveWorkspace(workspace);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-area">
          <img
            src="/ELIOS_SAR_logo.svg"
            alt="ELIOS-SAR"
            className="brand-logo"
          />
        </div>

        <nav className="workspace-bar">
          {Object.keys(WORKSPACES).map((ws) => (
            <button
              key={ws}
              type="button"
              className={activeWorkspace === ws ? "workspace-tab active" : "workspace-tab"}
              onClick={() => changeWorkspace(ws)}
            >
              {ws}
            </button>
          ))}
        </nav>

        <div className="header-status">
          <VehicleSelector
            vehicles={vehicles}
            value={selectedVehicleId}
            onChange={setSelectedVehicleId}
          />
          <span className="status-dot" />
          <span className={gcsConnected ? "connection-status online" : "connection-status offline"}>
            {gcsConnected ? "GCS LINK" : "GCS OFFLINE"}
          </span>
        </div>
      </header>

      <main className="workspace-area">
        <GridLayout
          className="gcs-grid"
          layouts={safeCurrentLayout}
          breakpoints={{
            lg: 1200,
            md: 996,
            sm: 768,
            xs: 480,
          }}
          cols={{
            lg: 12,
            md: 12,
            sm: 6,
            xs: 4,
          }}
          rowHeight={42}
          margin={[8, 8]}
          containerPadding={[8, 8]}
          compactType={activeWorkspace === "Operations" ? null : "vertical"}
          preventCollision={activeWorkspace === "Operations"}
          isDraggable={true}
          isResizable={true}
          draggableHandle=".panel-drag-handle"
          resizeHandles={["se"]}
          useCSSTransforms={true}
          measureBeforeMount={true}
          onLayoutChange={handleLayoutChange}
        >
          {activePanels.map((panel) => (
            <div key={panel.id}>
              <PanelWindow
                id={panel.id}
                title={panel.title}
                onClose={closePanel}
                isFullscreen={fullscreenPanelId === panel.id}
                onToggleFullscreen={toggleFullscreen}
              >
                <PanelContent
                  type={panel.type}
                  gcsState={gcsState}
                  gcsConnected={gcsConnected}
                  selectedVehicleId={selectedVehicleId}
                  selectedMissionId={selectedMissionId}
                  onSelectMission={setSelectedMissionId}
                  controlAuthority={controlAuthority}
                  commandBusy={commandBusy}
                  drones={drones}
                  selectedDroneId={selectedDroneId}
                  setSelectedDroneId={setSelectedDroneId}
                  rover={selectedRover}
                  roverSpeed={roverSpeed}
                  setRoverSpeed={setRoverSpeed}
                  commandLog={commandLog}
                  environmentHistory={environmentHistory}
                  systemEvents={systemEvents}
                  vehicles={vehicles}
                  onEnableControl={handleEnableControl}
                  onDisableControl={handleDisableControl}
                  onEmergencyStop={handleEmergencyStop}
                  onDroneCommand={handleDroneCommand}
                  onRoverCommand={handleRoverCommand}
                />
              </PanelWindow>
            </div>
          ))}
        </GridLayout>

        {activeFullscreenPanel && (
          <PanelWindow
            id={activeFullscreenPanel.id}
            title={activeFullscreenPanel.title}
            isFullscreen={true}
            onToggleFullscreen={toggleFullscreen}
            onClose={() => closePanel(activeFullscreenPanel.id)}
          >
            <PanelContent
              type={activeFullscreenPanel.type}
              gcsState={gcsState}
              gcsConnected={gcsConnected}
              selectedVehicleId={selectedVehicleId}
              selectedMissionId={selectedMissionId}
              onSelectMission={setSelectedMissionId}
              controlAuthority={controlAuthority}
              commandBusy={commandBusy}
              drones={drones}
              selectedDroneId={selectedDroneId}
              setSelectedDroneId={setSelectedDroneId}
              rover={selectedRover}
              roverSpeed={roverSpeed}
              setRoverSpeed={setRoverSpeed}
              commandLog={commandLog}
              environmentHistory={environmentHistory}
              systemEvents={systemEvents}
              vehicles={vehicles}
              onEnableControl={handleEnableControl}
              onDisableControl={handleDisableControl}
              onEmergencyStop={handleEmergencyStop}
              onDroneCommand={handleDroneCommand}
              onRoverCommand={handleRoverCommand}
            />
          </PanelWindow>
        )}
      </main>

      <footer className="status-bar">
        {/* ROVER */}
        <div className="status-item">
          <span
            className={`status-dot ${
              Object.keys(gcsState.vehicles ?? {}).some((id) => {
                const v = gcsState.vehicles[id];
                return (
                  (v?.type === "rover" ||
                    v?.vehicleType === "rover" ||
                    id.toLowerCase().includes("rover")) &&
                  v?.connected !== false
                );
              })
                ? "online"
                : "offline"
            }`}
          />
          <span>
            ROVER{" "}
            {Object.keys(gcsState.vehicles ?? {})
              .find((id) => {
                const vehicle = gcsState.vehicles[id];
                return (
                  vehicle?.type === "rover" ||
                  vehicle?.vehicleType === "rover" ||
                  id.toLowerCase().includes("rover")
                );
              })
              ?.toUpperCase() ?? "ROVER"}
          </span>
          <span
            className={
              Object.keys(gcsState.vehicles ?? {}).some((id) => {
                const v = gcsState.vehicles[id];
                return (
                  (v?.type === "rover" ||
                    v?.vehicleType === "rover" ||
                    id.toLowerCase().includes("rover")) &&
                  v?.connected !== false
                );
              })
                ? "status-value online"
                : "status-value offline"
            }
          >
            {Object.keys(gcsState.vehicles ?? {}).some((id) => {
              const v = gcsState.vehicles[id];
              return (
                (v?.type === "rover" ||
                  v?.vehicleType === "rover" ||
                  id.toLowerCase().includes("rover")) &&
                v?.connected !== false
              );
            })
              ? "ONLINE"
              : "OFFLINE"}
          </span>
        </div>

        {/* ROS / SIMULATION */}
        <div className="status-item">
          <span className={`status-dot ${gcsConnected ? "online" : "offline"}`} />
          <span>{gcsConnected ? "ROS LIVE" : "SIMULATION"}</span>
        </div>

        {/* PX4 */}
        <div className="status-item">
          <span className={`status-dot ${px4.connected ? "online" : "offline"}`} />
          <span>PX4</span>
          <span className={`status-value ${px4.connected ? "online" : "offline"}`}>
            {px4.connected ? "CONNECTED" : "NOT DETECTED"}
          </span>
        </div>

        {/* DRONE */}
        <div className="status-item">
          <span className={`status-dot ${px4.armed ? "offline" : "online"}`} />
          <span>DRONE</span>
          <span className={`status-value ${px4.armed ? "offline" : "online"}`}>
            {px4.armed ? "ARMED" : "DISARMED"}
          </span>
        </div>

        {/* GCS CONTROL */}
        <div className="status-item">
          <span className={`status-dot ${controlEnabled? "offline" : "online"}`} />
          <span>GCS CONTROL</span>
          <span className={`status-value ${controlEnabled? "offline" : "online"}`}>
            {controlEnabled? "ARMED" : "LOCKED"}
          </span>
        </div>

        {/* ALERTS */}
        <div className="status-item">
          <span className={`status-dot ${alerts.length > 0 ? "offline" : "online"}`} />
          <span className={alerts.length > 0 ? "status-value offline" : "status-value online"}>
            {alerts.length} ALERT{alerts.length === 1 ? "" : "S"}
          </span>
        </div>

        {/* RESET WORKSPACE */}
        <div className="status-item">
          <button
            type="button"
            onClick={resetWorkspace}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--ui-text-dim)",
              cursor: "pointer",
              fontSize: "inherit",
              padding: 0,
            }}
          >
            RESET WORKSPACE
          </button>
        </div>

        {/* CLOCK */}
        <div className="status-clock">
          {clock.toLocaleTimeString("en-GB", {
            hour12: false,
          })}{" "}
          IST
        </div>
      </footer>
    </div>
  );
}

export default App;
