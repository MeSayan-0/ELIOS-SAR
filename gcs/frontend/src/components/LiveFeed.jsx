import { useMemo, useState } from "react";

export default function LiveFeed({
  title = "LIVE RECON",
  vehicles = [],
  selectedVehicleId = null,
  liveImages = {},
}) {
  const vehicleList = Array.isArray(vehicles)
    ? vehicles
    : Object.values(vehicles || {});

  const selectedVehicle = useMemo(
    () =>
      vehicleList.find(
        (vehicle) =>
          (vehicle.vehicleId || vehicle.vehicle_id || vehicle.id) === selectedVehicleId
      ) || null,
    [vehicleList, selectedVehicleId]
  );

  const [mode, setMode] = useState("split");

  const [source, setSource] = useState(
    selectedVehicle?.vehicleType ||
      selectedVehicle?.vehicle_type ||
      "drone"
  );

  const availableSources = useMemo(() => {
    const sources = vehicleList
      .map((vehicle) => ({
        id: vehicle.vehicleId || vehicle.vehicle_id || vehicle.id,
        type: (
          vehicle.vehicleType ||
          vehicle.vehicle_type ||
          ""
        ).toLowerCase(),
      }))
      .filter((vehicle) => vehicle.id);

    if (sources.length === 0 && Object.keys(liveImages || {}).length > 0) {
      return [{ id: "DRONE-01", type: "drone" }];
    }

    return sources;
  }, [vehicleList, liveImages]);

  const sourceVehicle =
    availableSources.find((vehicle) => vehicle.type === source) ||
    availableSources[0] ||
    null;

  const actualSource =
    sourceVehicle?.type ||
    source ||
    "drone";

  const sourceId = sourceVehicle?.id;

  const prefix =
    actualSource === "rover"
      ? "rover"
      : "drone";

  const rgbUrl =
    liveImages?.[`${prefix}-rgb`] ||
    liveImages?.[`${sourceId}-rgb`] ||
    null;

  const thermalUrl =
    liveImages?.[`${prefix}-thermal`] ||
    liveImages?.[`${sourceId}-thermal`] ||
    null;

  function renderRgb() {
    return (
      <div
        className="recon-feed-frame recon-feed-rgb"
        style={
          rgbUrl
            ? {
                backgroundImage: `url("${rgbUrl}")`,
              }
            : undefined
        }
      >
        {!rgbUrl && (
          <>
            <div className="recon-rgb-glare" />
            <div className="recon-scanlines" />
            <div className="recon-no-signal">
              NO RGB SIGNAL
            </div>
          </>
        )}

        <div className="recon-frame-label">
          {actualSource.toUpperCase()} • RGB
        </div>

        <div className="recon-reticle">
          <span />
          <span />
        </div>
      </div>
    );
  }

  function renderThermal() {
    return (
      <div
        className="recon-feed-frame recon-feed-thermal"
        style={
          thermalUrl
            ? {
                backgroundImage: `url("${thermalUrl}")`,
              }
            : undefined
        }
      >
        {!thermalUrl && (
          <>
            <div className="recon-thermal-glare" />
            <div className="recon-scanlines" />
            <div className="recon-no-signal">
              NO THERMAL SIGNAL
            </div>
          </>
        )}

        <div className="recon-frame-label">
          {actualSource.toUpperCase()} • THERMAL
        </div>

        <div className="recon-reticle">
          <span />
          <span />
        </div>
      </div>
    );
  }

  if (availableSources.length === 0) {
    return (
      <div className="live-feed-empty">
        <div className="live-feed-empty-glow" />

        <div className="live-feed-empty-content">
          <strong>NO VEHICLE CONNECTED</strong>
          <span>
            Connect a drone or rover to view live reconnaissance.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="live-feed">
      <div className="live-feed-toolbar">

        <div className="live-feed-source-buttons">
          {availableSources
            .filter(
              (vehicle, index, array) =>
                array.findIndex(
                  (item) => item.type === vehicle.type
                ) === index
            )
            .map((vehicle) => (
              <button
                key={vehicle.type}
                type="button"
                className={
                  actualSource === vehicle.type
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setSource(vehicle.type)
                }
              >
                {vehicle.type.toUpperCase()} CAM
              </button>
            ))}
        </div>

        <div className="live-feed-mode-buttons">

          <button
            type="button"
            className={
              mode === "camera"
                ? "active"
                : ""
            }
            onClick={() =>
              setMode("camera")
            }
          >
            RGB
          </button>

          <button
            type="button"
            className={
              mode === "thermal"
                ? "active"
                : ""
            }
            onClick={() =>
              setMode("thermal")
            }
          >
            THERMAL
          </button>

          <button
            type="button"
            className={
              mode === "split"
                ? "active"
                : ""
            }
            onClick={() =>
              setMode("split")
            }
          >
            SPLIT
          </button>

        </div>
      </div>

      <div
        className={`live-feed-view live-feed-${mode}`}
      >
        {mode === "camera" &&
          renderRgb()}

        {mode === "thermal" &&
          renderThermal()}

        {mode === "split" && (
          <>
            {renderRgb()}
            {renderThermal()}
          </>
        )}
      </div>
    </div>
  );
}
