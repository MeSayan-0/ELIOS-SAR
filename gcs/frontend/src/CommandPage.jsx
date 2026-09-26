import React from "react";

export default function CommandPage({
  controlAuthority,
  commandBusy,

  drones = [],
  selectedDroneId,
  setSelectedDroneId,

  rover,
  roverSpeed = 0.5,
  setRoverSpeed,

  commandLog = [],

  onEnableControl,
  onDisableControl,
  onEmergencyStop,

  onDroneCommand,
  onRoverCommand,
}) {
  const controlEnabled = Boolean(controlAuthority?.enabled);

  return (
    <div className="command-console">
      {/* ======================================================
          CONTROL AUTHORITY
          ====================================================== */}
      <section className="command-authority">
        <div className="command-authority-copy">
          <h2 className="command-authority-title">
            GCS Control Authority.
          </h2>
          <p className="command-authority-text">
            The ground control station controls all vehicle commands
            and operations. Enable control to send commands.
            Emergency stop overrides all operations immediately.
          </p>
        </div>

        <div className="command-authority-actions">
          {!controlEnabled ? (
            <button
              type="button"
              className="command-enable"
              onClick={onEnableControl}
              disabled={commandBusy}
            >
              <span>♙</span>
              ENABLE GCS CONTROL
            </button>
          ) : (
            <button
              type="button"
              className="command-enable"
              onClick={onDisableControl}
              disabled={commandBusy}
            >
              <span>♙</span>
              DISABLE GCS CONTROL
            </button>
          )}

          <button
            type="button"
            className="command-estop"
            onClick={onEmergencyStop}
            disabled={commandBusy}
          >
            <span>⚠</span>
            EMERGENCY STOP
          </button>
        </div>
      </section>

      {/* ======================================================
          DRONE + ROVER
          ====================================================== */}
      <div className="command-control-grid">
        {/* ====================================================
            DRONE CONTROL
            ==================================================== */}
        <section className="command-card">
          <h2 className="command-card-title">
            DRONE CONTROL
          </h2>

          <div className="command-field">
            <label className="command-field-label">
              Active Drone
            </label>
            <select
              className="command-select"
              value={selectedDroneId || ""}
              onChange={(e) => setSelectedDroneId?.(e.target.value)}
              disabled={!drones.length || commandBusy}
            >
              {!drones.length && (
                <option value="">NO DRONES</option>
              )}
              {drones.map((drone) => {
                const id = drone.vehicleId || drone.id;
                return (
                  <option key={id} value={id}>
                    {id}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="command-button-grid">
            <button
              type="button"
              className="command-button arm"
              onClick={() => onDroneCommand?.("ARM")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>♙</span>
              ARM
            </button>

            <button
              type="button"
              className="command-button"
              onClick={() => onDroneCommand?.("DISARM")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>♙</span>
              DISARM
            </button>

            <button
              type="button"
              className="command-button arm"
              onClick={() => onDroneCommand?.("OFFBOARD")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>⚡</span>
              OFFBOARD
            </button>

            <button
              type="button"
              className="command-button amber"
              onClick={() => onDroneCommand?.("TAKEOFF")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>↑</span>
              TAKEOFF
            </button>

            <button
              type="button"
              className="command-button arm"
              onClick={() => onDroneCommand?.("HOVER")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>Ⅱ</span>
              HOVER
            </button>

            <button
              type="button"
              className="command-button amber"
              onClick={() => onDroneCommand?.("LAND")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>↓</span>
              LAND
            </button>

            <button
              type="button"
              className="command-button amber"
              onClick={() => onDroneCommand?.("RTL")}
              disabled={!controlEnabled || commandBusy || !selectedDroneId}
            >
              <span>⌂</span>
              RETURN TO LAUNCH
            </button>
          </div>
        </section>

        {/* ====================================================
            ROVER CONTROL
            ==================================================== */}
        <section className="command-card">
          <h2 className="command-card-title">
            ROVER CONTROL
          </h2>

          <div className="rover-speed-row">
            <span className="rover-speed-label">
              Speed
            </span>
            <input
              className="rover-speed-slider"
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={roverSpeed}
              onChange={(e) => setRoverSpeed?.(Number(e.target.value))}
            />
            <span className="rover-speed-value">
              {Number(roverSpeed).toFixed(1)} m/s
            </span>
          </div>

          <div className="rover-direction-pad">
            <button
              type="button"
              className="rover-direction-button rover-up"
              onClick={() => onRoverCommand?.("FORWARD")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              ↑
            </button>

            <button
              type="button"
              className="rover-direction-button rover-left"
              onClick={() => onRoverCommand?.("LEFT")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              ←
            </button>

            <button
              type="button"
              className="rover-direction-button rover-stop stop"
              onClick={() => onRoverCommand?.("STOP")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              □
            </button>

            <button
              type="button"
              className="rover-direction-button rover-right"
              onClick={() => onRoverCommand?.("RIGHT")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              →
            </button>

            <button
              type="button"
              className="rover-direction-button rover-down"
              onClick={() => onRoverCommand?.("BACK")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              ↓
            </button>
          </div>

          <div className="rover-actions">
            <button
              type="button"
              className="rover-action"
              onClick={() => onRoverCommand?.("DOCK")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              ⌂ &nbsp; DOCK DRONE
            </button>

            <button
              type="button"
              className="rover-action secondary"
              onClick={() => onRoverCommand?.("UNDOCK")}
              disabled={!controlEnabled || commandBusy || !rover}
            >
              ♙ &nbsp; UNDOCK
            </button>
          </div>
        </section>
      </div>

      {/* ======================================================
          COMMAND LOG
          ====================================================== */}
      <section className="command-log">
        <h2 className="command-log-title">
          COMMAND LOG
        </h2>

        <div className="command-log-table">
          <table>
            <thead>
              <tr>
                <th>TIME</th>
                <th>VEHICLE</th>
                <th>COMMAND</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {commandLog.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: "16px", color: "var(--text-muted)" }}>
                    NO COMMANDS RECORDED
                  </td>
                </tr>
              ) : (
                commandLog.map((entry, index) => {
                  const id = entry.commandId || entry._id || entry.id || index;
                  const rawTime = entry.createdAt || entry.timestamp || entry.time;
                  const timeStr = rawTime
                    ? (typeof rawTime === "string" && rawTime.includes(":") && !rawTime.includes("T")
                        ? rawTime
                        : new Date(rawTime).toLocaleTimeString("en-GB", { hour12: false }))
                    : "--:--:--";
                  const vehicleStr = entry.vehicleId || entry.vehicle || "—";
                  const commandStr = entry.command || "—";
                  const statusStr = String(entry.status || "UNKNOWN").toUpperCase();

                  const statusClass =
                    statusStr === "ACCEPTED" || statusStr === "COMPLETED"
                      ? "command-status-success"
                      : statusStr === "ERROR" || statusStr === "FAILED" || statusStr === "REJECTED"
                      ? "command-status-error"
                      : "command-status-pending";

                  return (
                    <tr key={id}>
                      <td>{timeStr}</td>
                      <td><strong>{vehicleStr}</strong></td>
                      <td>{commandStr}</td>
                      <td className={statusClass}>{statusStr}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
