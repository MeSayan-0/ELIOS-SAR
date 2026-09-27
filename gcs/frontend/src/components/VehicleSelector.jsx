export default function VehicleSelector({
  vehicles,
  value,
  onChange,
}) {
  if (
    !vehicles ||
    vehicles.length === 0
  ) {
    return (
      <div className="vehicle-selector empty">
        <span>NO VEHICLES</span>
      </div>
    );
  }

  return (
    <select
      className="vehicle-selector"
      value={value ?? ""}
      onChange={(event) =>
        onChange(
          event.target.value || null
        )
      }
    >
      {vehicles.map((vehicle) => {
        const id =
          vehicle.vehicleId ??
          vehicle.vehicle_id;

        const type =
          vehicle.vehicleType ??
          vehicle.vehicle_type ??
          "UNKNOWN";

        return (
          <option
            key={id}
            value={id}
          >
            {String(id).toUpperCase()} (
            {String(type).toUpperCase()})
          </option>
        );
      })}
    </select>
  );
}
